"""Run the Task 1.2 convergence grid on a Vultr VM through the Vultr API, then destroy the VM.

One command does create -> wait -> upload repo -> run cloud/vultr_sweep.sh -> download
results -> delete. The VM is deleted in a `finally` block, so a crash or Ctrl-C still
stops the billing (check https://my.vultr.com/ afterwards anyway).

    export VULTR_API_KEY=...                      # my.vultr.com -> Account -> API; never commit it
    python cloud/vultr_run.py --list-plans        # cheapest plans with >= 16 vCPU in the region
    python cloud/vultr_run.py --plan <plan-id>    # the full run (~20-30 min)
    python cloud/vultr_run.py --cleanup           # delete any VM this script left behind

Safety: asks before creating; refuses if one of our VMs already exists; --max-minutes hard
stop (default 90); deletes on success, error, Ctrl-C, closed terminal or kill. Only a laptop
that sleeps or loses power mid-run can skip the delete -- then run --cleanup.

Needs an SSH key at ~/.ssh/id_ed25519.pub (or pass --pubkey); it is registered with Vultr once.
Only the committed code is uploaded (git archive HEAD), so no secrets leave the laptop.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:                                   # pip install truststore: use the macOS/Windows system
    import truststore                  # certificate store (fixes CERTIFICATE_VERIFY_FAILED with
    truststore.inject_into_ssl()       # python.org builds and on networks that inspect TLS)
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from tools_log import log_tool  # noqa: E402

API = "https://api.vultr.com/v2"
SSH = ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10",
       "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=4"]   # a dead link fails in ~2 min
TAG = "duquantum"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {os.environ['VULTR_API_KEY']}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Vultr API {method} {path}: {e.code} {e.read().decode()[:300]}\n"
                         "(401 'Unauthorized IP address' -> add your IP under Account -> API -> Access Control)")


def plans(region, min_vcpu):
    ps = call("GET", "/plans?type=all&per_page=500")["plans"]
    ok = [p for p in ps if p["vcpu_count"] >= min_vcpu and region in p["locations"]]
    return sorted(ok, key=lambda p: p["monthly_cost"])


def ubuntu_os_id():
    for o in call("GET", "/os?per_page=500")["os"]:
        if o["name"].startswith("Ubuntu 24.04") and o["arch"] == "x64":
            return o["id"]
    raise SystemExit("Ubuntu 24.04 x64 image not found")


def ssh_key_id(pubkey):
    text = Path(pubkey).expanduser().read_text().strip()
    for k in call("GET", "/ssh-keys?per_page=500")["ssh_keys"]:
        if k["ssh_key"].strip() == text:
            return k["id"]
    return call("POST", "/ssh-keys", {"name": "duquantum", "ssh_key": text})["ssh_key"]["id"]


def wait_ready(iid, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        inst = call("GET", f"/instances/{iid}")["instance"]
        print(f"  {int(time.time() - t0):4d} s  status={inst['status']} server={inst['server_status']} ip={inst['main_ip']}",
              flush=True)
        if inst["status"] == "active" and inst["server_status"] == "ok" and inst["main_ip"] != "0.0.0.0":
            ip = inst["main_ip"]
            for _ in range(30):          # sshd comes up a little after the API says "ok"
                if subprocess.run(SSH + [f"root@{ip}", "true"], capture_output=True).returncode == 0:
                    return ip
                time.sleep(10)
        time.sleep(15)
    raise TimeoutError("instance did not become reachable")


def credit_left():
    """Unspent credit in USD: Vultr shows credit as a negative balance; pending charges are this month's usage."""
    acc = call("GET", "/account")["account"]
    return -float(acc["balance"]) - float(acc["pending_charges"])


def check_reserve(max_cost, reserve):
    """Refuse a run whose worst case would leave less than `reserve` dollars of credit."""
    left = credit_left()
    print(f"credit left ${left:.2f}; this run costs at most ${max_cost:.2f}; "
          f"keeping at least ${reserve:g} in reserve", flush=True)
    if left - max_cost < reserve:
        raise SystemExit("refusing: the worst case would dip into the reserve. "
                         "Lower --max-minutes/--budget or --servers.")


def ours():
    return call("GET", f"/instances?tag={TAG}&per_page=500")["instances"]


def delete(iid):
    """Delete with retries; if it still fails, say loudly how to clean up."""
    for i in range(6):
        try:
            call("DELETE", f"/instances/{iid}")
            return True
        except (SystemExit, OSError) as e:
            print(f"delete failed ({e}); retrying in {10 * (i + 1)} s", flush=True)
            time.sleep(10 * (i + 1))
    print(f"\n!!! COULD NOT DELETE {iid}. IT IS STILL BILLING. Run: python cloud/vultr_run.py --cleanup\n"
          "!!! or delete it at https://my.vultr.com/subs/", flush=True)
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", help="plan id from --list-plans")
    p.add_argument("--region", default="ewr", help="ewr = New Jersey, closest to Durham")
    p.add_argument("--min-vcpu", type=int, default=16)
    p.add_argument("--pubkey", default="~/.ssh/id_ed25519.pub")
    p.add_argument("--jobs", type=int, help="parallel runs on the VM (default vCPU/4)")
    p.add_argument("--max-minutes", type=float, default=90, help="hard stop: delete the VM after this long")
    p.add_argument("--reserve", type=float, default=50, help="never let credit drop below this (USD)")
    p.add_argument("--list-plans", action="store_true")
    p.add_argument("--cleanup", action="store_true", help="delete every VM this script created, then exit")
    a = p.parse_args()
    if not os.environ.get("VULTR_API_KEY"):
        raise SystemExit("set VULTR_API_KEY in your shell first (never commit it)")

    if a.cleanup:
        for inst in ours():
            print("deleting", inst["id"], inst["label"], inst["main_ip"], flush=True)
            delete(inst["id"])
        print("no duquantum VMs left" if not ours() else "some VMs remain, check https://my.vultr.com/subs/")
        return

    if a.list_plans or not a.plan:
        for pl in plans(a.region, a.min_vcpu)[:10]:
            print(f"{pl['id']:28s} {pl['vcpu_count']:3d} vCPU {pl['ram'] // 1024:4d} GB  "
                  f"${pl['monthly_cost']}/mo (~${pl['monthly_cost'] / 730:.2f}/h)")
        if not a.plan:
            print("\nre-run with --plan <id>")
        return

    if ours():
        raise SystemExit("a duquantum VM already exists; run --cleanup first so we never pay for two")
    pl = next((x for x in plans(a.region, 1) if x["id"] == a.plan), None)
    if pl:
        print(f"{a.plan}: ~${pl['monthly_cost'] / 730:.2f}/h, at most ~${pl['monthly_cost'] / 730 * a.max_minutes / 60:.2f} "
              f"with --max-minutes {a.max_minutes:g}", flush=True)
    if pl:
        check_reserve(pl["monthly_cost"] / 730 * a.max_minutes / 60, a.reserve)
    if input("create the VM? [y/N] ").strip().lower() != "y":
        return
    iid = call("POST", "/instances", {
        "region": a.region, "plan": a.plan, "os_id": ubuntu_os_id(),
        "sshkey_id": [ssh_key_id(a.pubkey)], "label": "duquantum-grid", "tags": ["duquantum"],
    })["instance"]["id"]
    print("created instance", iid, flush=True)
    t0 = time.time()

    def stop(signum, _frame):         # closing the terminal (SIGHUP) or kill (SIGTERM) still deletes
        raise SystemExit(f"got signal {signum}, deleting the VM")
    signal.signal(signal.SIGHUP, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        ip = wait_ready(iid)
        print("uploading committed code to", ip, flush=True)
        archive = subprocess.run(["git", "archive", "HEAD"], cwd=ROOT, capture_output=True, check=True).stdout
        subprocess.run(SSH + [f"root@{ip}", "mkdir -p repo && tar -x -C repo"], input=archive, check=True)
        jobs = f"JOBS={a.jobs} " if a.jobs else ""
        left = a.max_minutes * 60 - (time.time() - t0)
        subprocess.run(SSH + [f"root@{ip}", f"cd repo && {jobs}./cloud/vultr_sweep.sh"], check=True, timeout=left)
        print("downloading results", flush=True)
        for sub in ["results", "figures"]:
            subprocess.run(["scp", "-r", "-o", "StrictHostKeyChecking=accept-new",
                            f"root@{ip}:repo/{sub}/.", str(ROOT / sub)], check=True)
        ok = True
    except BaseException:
        ok = False
        raise
    finally:
        mins = (time.time() - t0) / 60
        deleted = delete(iid)
        if deleted:
            print(f"deleted instance {iid} after {mins:.1f} min "
                  "(confirm at https://my.vultr.com/subs/)", flush=True)
        cost = f"~${pl['monthly_cost'] / 730 * mins / 60:.2f}" if pl else "see Vultr billing"
        log_tool("Vultr (API v2)",
                 "Task 1.2 (Na, Nb) convergence grid via `cloud/vultr_run.py`",
                 f"`{a.plan}`, region {a.region}, {mins:.0f} min, {cost}; VM "
                 + ("deleted" if deleted else "NOT deleted, run --cleanup"),
                 "`results/grid.log`, `results/task_1_2_grid.json`, `figures/task_1_2_grid.png`",
                 "completed" if ok else "failed or interrupted; see terminal output")


if __name__ == "__main__":
    main()
