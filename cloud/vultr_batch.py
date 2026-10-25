"""Run a list of independent jobs across several Vultr VMs, under a hard dollar cap.

    python cloud/vultr_batch.py grid --servers 3 --plan voc-c-16c-32gb-300s-amd --budget 5
    python cloud/vultr_batch.py jobs.txt --servers 4 --plan <id> --budget 10
    python cloud/vultr_batch.py cloud/s2_batch3s.txt --branch main --servers 3 --plan <id> --budget 20
    caffeinate -i python cloud/vultr_batch.py ... --yes --push     # unattended: no prompt, results pushed

--branch runs the committed code of origin/<branch> (fetched first) and reads the jobs file
from that branch, so the laptop can stay on any branch. Results are copied into a worktree of
that branch (.cloud-worktrees/), and --push commits them there with the tools-log row and pushes.
A job that fails does not stop the others; failures are counted in the log row. If the account's
instance limit is lower than --servers, the jobs are spread over the VMs it did create.

A jobs file has one shell command per line, run from the repo root with the VM's .venv
(`python` means .venv/bin/python). An optional leading weight, `3<TAB>command`, is the
job's relative cost; jobs are spread so every server gets about the same total weight.
`grid` is the Task 1.2 (Na, Nb) grid, weighted by (Na*Nb)^3.

Each VM runs about vCPU/4 jobs at once and logs every job's wall time to
results/batch-<vm>.log, which is what we use to estimate the next run's cost.
Budget: the run is stopped and every VM deleted once `servers x hourly x elapsed`
reaches --budget. VMs are deleted on success, error, Ctrl-C, closed terminal or kill;
a laptop that sleeps mid-run is the one case to fix with `vultr_run.py --cleanup`.
"""
import argparse
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vultr_run import (ROOT, SSH, TAG, call, check_reserve, delete, log_tool, ours,  # noqa: E402
                       plans, ssh_key_id, ubuntu_os_id, wait_ready)


REF = "HEAD"                           # what gets uploaded; origin/<branch> with --branch


def load_jobs(spec):
    if spec == "grid":
        out = subprocess.run([sys.executable, "-m", "tasks.task_1_2_grid", "--list"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split("\n")
        return [((int(a) * int(b)) ** 3 / 1e6, f"python -m tasks.task_1_2_grid --point {a} {b}")
                for a, b in (line.split() for line in out if line.strip())]
    jobs = []
    text = (Path(spec).read_text() if REF == "HEAD" else
            subprocess.run(["git", "show", f"{REF}:{spec}"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout)
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            w, _, cmd = line.partition("\t") if "\t" in line else ("1", "", line)
            jobs.append((float(w), cmd.strip()))
    return jobs


def shard(jobs, n, slots=4):
    """Longest job first onto the least-loaded lane; each VM has `slots` lanes (parallel jobs).

    A VM's finish time is roughly its busiest lane, so four long jobs share one VM instead of
    each taking a whole VM while three of its lanes sit idle.
    """
    lanes = [[0.0, k] for k in range(n) for _ in range(slots)]
    out = [[] for _ in range(n)]
    for w, cmd in sorted(jobs, key=lambda j: -j[0]):
        lane = min(lanes, key=lambda x: (x[0], x[1]))
        lane[0] += w
        out[lane[1]].append(cmd)
    return out


def makespan(jobs, shards, slots):
    """Estimated finish time per VM (weight units), simulating `slots` parallel lanes."""
    w = {c: x for x, c in jobs}
    est = []
    for s in shards:
        lanes = [0.0] * slots
        for c in s:
            i = lanes.index(min(lanes))
            lanes[i] += w[c]
        est.append(max(lanes) if s else 0.0)
    return est

def download(ip, dest):
    # only files written during the run: the uploaded snapshot also holds every other VM's
    # earlier logs and results, and copying those back would overwrite fresher ones
    pack = subprocess.run(SSH + [f"root@{ip}", "cd repo && find results figures -type f -newer .t0 -print0 "
                                 "| tar --null -cf - -T -"], capture_output=True, check=True, timeout=120).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=pack, check=True)


def run_vm(k, iid, cmds, jobs_per_vm, deadline, status, dest):
    ip = wait_ready(iid)
    status[k] = "setup"
    archive = subprocess.run(["git", "archive", REF], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(SSH + [f"root@{ip}", "mkdir -p repo && tar -x -C repo"], input=archive, check=True)
    lines = "\n".join(c.replace("python ", ".venv/bin/python ", 1) if c.startswith("python ") else c
                      for c in cmds) + "\n"
    subprocess.run(SSH + [f"root@{ip}", "cat > repo/jobs.txt"], input=lines.encode(), check=True)
    par = f"{jobs_per_vm}" if jobs_per_vm else "$(( $(nproc) / 4 > 0 ? $(nproc) / 4 : 1 ))"
    # a failing job does not stop the others: xargs keeps going, and the pipe's status is tee's
    # PATH as well, so `python` resolves to the venv even after an `ENV=1 python ...` prefix
    remote = (f"cd repo && ./cloud/setup_vm.sh && mkdir -p results figures && touch .t0 && export PATH=$PWD/.venv/bin:$PATH && "
              f"xargs -P {par} -d '\\n' -I CMD sh -c 's=$(date +%s); CMD; "
              f"echo \"JOB $? $(( $(date +%s) - s ))s CMD\"' < jobs.txt 2>&1 | tee results/batch-vm{k}.log")
    status[k] = "running"
    try:
        subprocess.run(SSH + [f"root@{ip}", remote], check=True,
                       timeout=max(60, deadline - time.time() - 300))   # leave 5 min to copy back
    finally:
        status[k] = "downloading"
        download(ip, dest)                 # partial results are still worth having
        status[k] = "done"


def job_failures(dest, n):
    bad = 0
    for k in range(n):
        f = dest / "results" / f"batch-vm{k}.log"
        if f.exists():
            bad += sum(1 for line in f.read_text().splitlines()
                       if line.startswith("JOB ") and not line.startswith("JOB 0 "))
    return bad


def push_results(dest, branch, message):
    """Commit the copied-back results on `branch` and push, retrying on a race with other pushes."""
    g = ["git", "-C", str(dest)]
    subprocess.run(g + ["add", "-A", "results", "figures", "docs/tools-log.md"], check=False)
    if subprocess.run(g + ["diff", "--cached", "--quiet"]).returncode == 0:
        print("nothing new to push")
        return
    subprocess.run(g + ["commit", "-q", "-m", message], check=True)
    for i in range(4):
        subprocess.run(g + ["pull", "-q", "--rebase", "origin", branch], check=False)
        if subprocess.run(g + ["push", "-q", "origin", f"HEAD:{branch}"]).returncode == 0:
            print(f"pushed results to origin/{branch}")
            return
        time.sleep(2 ** (i + 1))
    print(f"!!! push failed; results are committed in {dest}, push them by hand")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("jobs", help="'grid' or a jobs file")
    p.add_argument("--plan", required=True)
    p.add_argument("--servers", type=int, default=2)
    p.add_argument("--budget", type=float, required=True, help="hard cap in USD for this run")
    p.add_argument("--max-minutes", type=float, default=180, help="time cap, whatever the budget")
    p.add_argument("--region", default="ewr")
    p.add_argument("--pubkey", default="~/.ssh/id_ed25519.pub")
    p.add_argument("--jobs-per-vm", type=int, help="parallel jobs per VM (default vCPU/4)")
    p.add_argument("--branch", help="run origin/<branch> instead of the local checkout")
    p.add_argument("--push", action="store_true",
                   help="commit results/ figures/ and the tools-log row to the branch and push")
    p.add_argument("--yes", action="store_true", help="don't ask before creating (the estimate is still printed)")
    p.add_argument("--reserve", type=float, default=50, help="never let credit drop below this (USD)")
    a = p.parse_args()
    global REF
    if a.branch:
        subprocess.run(["git", "fetch", "-q", "origin", a.branch], cwd=ROOT, check=True)
        REF = f"origin/{a.branch}"

    jobs = load_jobs(a.jobs)
    pl = next((x for x in plans(a.region, 1) if x["id"] == a.plan), None)
    if not pl:
        raise SystemExit(f"plan {a.plan} not offered in {a.region}; see vultr_run.py --list-plans")
    slots = a.jobs_per_vm or max(1, pl.get("vcpu_count", 16) // 4)
    shards = [s for s in shard(jobs, a.servers, slots) if s]
    hourly = pl["monthly_cost"] / 730
    minutes = min(a.budget / (len(shards) * hourly) * 60, a.max_minutes)
    print(f"{len(jobs)} jobs on {len(shards)} x {a.plan} (~${hourly:.2f}/h each); "
          f"everything stops after {minutes:.0f} min (at most ${len(shards) * hourly * minutes / 60:.2f})")
    for k, (s, m) in enumerate(zip(shards, makespan(jobs, shards, slots))):
        print(f"  vm{k}: {len(s):2d} jobs, ~{m:.0f} weight units with {slots} in parallel")
    check_reserve(len(shards) * hourly * minutes / 60, a.reserve)
    if ours():
        raise SystemExit("duquantum VMs already exist; run `python cloud/vultr_run.py --cleanup` first")
    if not a.yes and input("create the VMs? [y/N] ").strip().lower() != "y":
        return

    # results go to the checkout of the branch that ran: here, or a worktree of --branch
    dest = ROOT
    if a.branch:
        dest = ROOT / ".cloud-worktrees" / a.branch.replace("/", "_")
        if dest.exists():
            subprocess.run(["git", "-C", str(dest), "checkout", "-q", "-B", f"cloud-results/{a.branch}", REF],
                           check=True)
            subprocess.run(["git", "-C", str(dest), "reset", "-q", "--hard", REF], check=True)
        else:
            # a separate local branch name, so a local `a.branch` with unpushed work is never touched
            subprocess.run(["git", "worktree", "add", "-q", "-B", f"cloud-results/{a.branch}", str(dest), REF],
                           cwd=ROOT, check=True)
        print("results will be copied into", dest)

    def stop(signum, _frame):
        raise SystemExit(f"got signal {signum}, deleting the VMs")
    signal.signal(signal.SIGHUP, stop)
    signal.signal(signal.SIGTERM, stop)

    ids, t0, ok, gone = [], time.time(), False, set()
    try:
        os_id, key = ubuntu_os_id(), ssh_key_id(a.pubkey)
        for k in range(len(shards)):
            try:
                ids.append(call("POST", "/instances", {
                    "region": a.region, "plan": a.plan, "os_id": os_id, "sshkey_id": [key],
                    "label": f"duquantum-vm{k}", "tags": [TAG]})["instance"]["id"])
            except SystemExit as e:        # e.g. the account's instance limit
                if not ids:
                    raise
                print(f"could only create {len(ids)} VMs ({e}); spreading the jobs over those", flush=True)
                shards = [s for s in shard(jobs, len(ids), slots) if s]
                break
            print(f"created vm{k} {ids[-1]}", flush=True)
        deadline = t0 + minutes * 60
        status, errors = {k: "booting" for k in range(len(shards))}, {}

        def worker(k):
            try:
                run_vm(k, ids[k], shards[k], a.jobs_per_vm, deadline, status, dest)
                if delete(ids[k]):               # stop paying for a VM as soon as its shard is home
                    gone.add(ids[k])
                    status[k] = "deleted"
            except BaseException as e:      # noqa: BLE001  report, the main thread deletes
                errors[k] = repr(e)
                status[k] = "failed"
        threads = [threading.Thread(target=worker, args=(k,), daemon=True) for k in range(len(shards))]
        for th in threads:
            th.start()
        while any(th.is_alive() for th in threads):
            spent = len(ids) * hourly * (time.time() - t0) / 3600
            print(f"  {int(time.time() - t0) // 60:3d} min  ${spent:.2f}/{a.budget:g}  {status}", flush=True)
            if time.time() > deadline + 60:       # workers stop themselves 5 min early to copy back
                raise SystemExit("budget reached, deleting the VMs")
            time.sleep(60)
        ok = not errors
        for k, e in errors.items():
            print(f"vm{k} failed: {e}")
    finally:
        mins = (time.time() - t0) / 60
        deleted = all([delete(i) for i in ids if i not in gone])
        cost = len(ids) * hourly * mins / 60
        print(f"deleted {len(ids)} VMs after {mins:.1f} min, ~${cost:.2f} "
              "(confirm at https://my.vultr.com/subs/)", flush=True)
        if ids:
            bad = job_failures(dest, len(ids))
            outcome = ("completed" if ok else "VM error or stopped early; partial results kept") + \
                      (f"; {bad} job(s) exited non-zero, see batch logs" if bad else "; all jobs exit 0")
            log_tool("Vultr (API v2, batch)", f"`{a.jobs}` ({REF}): {len(jobs)} jobs via `cloud/vultr_batch.py`",
                     f"{len(ids)} x `{a.plan}`, {mins:.0f} min, ~${cost:.2f} of ${a.budget:g} cap; VMs "
                     + ("deleted" if deleted else "NOT all deleted, run --cleanup"),
                     "`results/batch-vm*.log` + job outputs", outcome,
                     log=dest / "docs" / "tools-log.md")
            if a.push:
                push_results(dest, a.branch or subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True,
                    text=True).stdout.strip(), f"Cloud batch results: {a.jobs}, {len(ids)} VMs, "
                    f"{mins:.0f} min, ~${cost:.2f}")


if __name__ == "__main__":
    main()
