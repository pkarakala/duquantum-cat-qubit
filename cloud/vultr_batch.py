"""Run a list of independent jobs across several Vultr VMs, under a hard dollar cap.

    python cloud/vultr_batch.py grid --servers 3 --plan voc-c-16c-32gb-300s-amd --budget 5
    python cloud/vultr_batch.py jobs.txt --servers 4 --plan <id> --budget 10
    python cloud/vultr_batch.py cloud/research_jobs.txt --branch research-runs --servers 4 --plan <id> --budget 20

--branch runs the committed code of origin/<branch> (fetched first) and reads the jobs file
from that branch, so the laptop can stay on any branch. Results land in this checkout.

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


def shard(jobs, n):
    """Longest job first onto the least-loaded server."""
    bins = [[0.0, []] for _ in range(n)]
    for w, cmd in sorted(jobs, key=lambda j: -j[0]):
        b = min(bins, key=lambda x: x[0])
        b[0] += w
        b[1].append(cmd)
    return [b[1] for b in bins]


def run_vm(k, iid, cmds, jobs_per_vm, deadline, status):
    ip = wait_ready(iid)
    status[k] = "setup"
    archive = subprocess.run(["git", "archive", REF], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(SSH + [f"root@{ip}", "mkdir -p repo && tar -x -C repo"], input=archive, check=True)
    lines = "\n".join(c.replace("python ", ".venv/bin/python ", 1) if c.startswith("python ") else c
                      for c in cmds) + "\n"
    subprocess.run(SSH + [f"root@{ip}", "cat > repo/jobs.txt"], input=lines.encode(), check=True)
    par = f"{jobs_per_vm}" if jobs_per_vm else "$(( $(nproc) / 4 > 0 ? $(nproc) / 4 : 1 ))"
    remote = (f"cd repo && ./cloud/setup_vm.sh && mkdir -p results && "
              f"xargs -P {par} -d '\\n' -I CMD sh -c 's=$(date +%s); CMD; "
              f"echo \"JOB $? $(( $(date +%s) - s ))s CMD\"' < jobs.txt 2>&1 | tee results/batch-vm{k}.log")
    status[k] = "running"
    subprocess.run(SSH + [f"root@{ip}", remote], check=True, timeout=max(60, deadline - time.time()))
    for sub in ["results", "figures"]:
        subprocess.run(["scp", "-q", "-r", "-o", "StrictHostKeyChecking=accept-new",
                        f"root@{ip}:repo/{sub}/.", str(ROOT / sub)], check=True)
    status[k] = "done"


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
    p.add_argument("--reserve", type=float, default=50, help="never let credit drop below this (USD)")
    a = p.parse_args()
    global REF
    if a.branch:
        subprocess.run(["git", "fetch", "-q", "origin", a.branch], cwd=ROOT, check=True)
        REF = f"origin/{a.branch}"

    jobs = load_jobs(a.jobs)
    shards = [s for s in shard(jobs, a.servers) if s]
    pl = next((x for x in plans(a.region, 1) if x["id"] == a.plan), None)
    if not pl:
        raise SystemExit(f"plan {a.plan} not offered in {a.region}; see vultr_run.py --list-plans")
    hourly = pl["monthly_cost"] / 730
    minutes = min(a.budget / (len(shards) * hourly) * 60, a.max_minutes)
    print(f"{len(jobs)} jobs on {len(shards)} x {a.plan} (~${hourly:.2f}/h each); "
          f"everything stops after {minutes:.0f} min (at most ${len(shards) * hourly * minutes / 60:.2f})")
    for k, s in enumerate(shards):
        print(f"  vm{k}: {len(s)} jobs")
    check_reserve(len(shards) * hourly * minutes / 60, a.reserve)
    if ours():
        raise SystemExit("duquantum VMs already exist; run `python cloud/vultr_run.py --cleanup` first")
    if input("create the VMs? [y/N] ").strip().lower() != "y":
        return

    def stop(signum, _frame):
        raise SystemExit(f"got signal {signum}, deleting the VMs")
    signal.signal(signal.SIGHUP, stop)
    signal.signal(signal.SIGTERM, stop)

    ids, t0, ok = [], time.time(), False
    try:
        os_id, key = ubuntu_os_id(), ssh_key_id(a.pubkey)
        for k in range(len(shards)):
            ids.append(call("POST", "/instances", {
                "region": a.region, "plan": a.plan, "os_id": os_id, "sshkey_id": [key],
                "label": f"duquantum-vm{k}", "tags": [TAG]})["instance"]["id"])
            print(f"created vm{k} {ids[-1]}", flush=True)
        deadline = t0 + minutes * 60
        status, errors = {k: "booting" for k in range(len(shards))}, {}

        def worker(k):
            try:
                run_vm(k, ids[k], shards[k], a.jobs_per_vm, deadline, status)
            except BaseException as e:      # noqa: BLE001  report, the main thread deletes
                errors[k] = repr(e)
                status[k] = "failed"
        threads = [threading.Thread(target=worker, args=(k,), daemon=True) for k in range(len(shards))]
        for th in threads:
            th.start()
        while any(th.is_alive() for th in threads):
            spent = len(ids) * hourly * (time.time() - t0) / 3600
            print(f"  {int(time.time() - t0) // 60:3d} min  ${spent:.2f}/{a.budget:g}  {status}", flush=True)
            if time.time() > deadline:
                raise SystemExit("budget reached, deleting the VMs")
            time.sleep(60)
        ok = not errors
        for k, e in errors.items():
            print(f"vm{k} failed: {e}")
    finally:
        mins = (time.time() - t0) / 60
        deleted = all([delete(i) for i in ids])
        cost = len(ids) * hourly * mins / 60
        print(f"deleted {len(ids)} VMs after {mins:.1f} min, ~${cost:.2f} "
              "(confirm at https://my.vultr.com/subs/)", flush=True)
        if ids:
            log_tool("Vultr (API v2, batch)", f"`{a.jobs}` ({REF}): {len(jobs)} jobs via `cloud/vultr_batch.py`",
                     f"{len(ids)} x `{a.plan}`, {mins:.0f} min, ~${cost:.2f} of ${a.budget:g} cap; VMs "
                     + ("deleted" if deleted else "NOT all deleted, run --cleanup"),
                     "`results/batch-vm*.log` + job outputs", "completed" if ok else "failed or stopped")


if __name__ == "__main__":
    main()
