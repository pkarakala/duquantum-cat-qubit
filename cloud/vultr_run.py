"""Run the Task 1.2 convergence grid on a Vultr VM through the Vultr API, then destroy the VM.

One command does create -> wait -> upload repo -> run cloud/vultr_sweep.sh -> download
results -> delete. The VM is deleted in a `finally` block, so a crash or Ctrl-C still
stops the billing (check https://my.vultr.com/ afterwards anyway).

    export VULTR_API_KEY=...                      # my.vultr.com -> Account -> API; never commit it
    python cloud/vultr_run.py --list-plans        # cheapest plans with >= 16 vCPU in the region
    python cloud/vultr_run.py --plan <plan-id>    # the full run (~20-30 min)

Needs an SSH key at ~/.ssh/id_ed25519.pub (or pass --pubkey); it is registered with Vultr once.
Only the committed code is uploaded (git archive HEAD), so no secrets leave the laptop.
"""
import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.vultr.com/v2"
SSH = ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10"]


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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", help="plan id from --list-plans")
    p.add_argument("--region", default="ewr", help="ewr = New Jersey, closest to Durham")
    p.add_argument("--min-vcpu", type=int, default=16)
    p.add_argument("--pubkey", default="~/.ssh/id_ed25519.pub")
    p.add_argument("--jobs", type=int, help="parallel runs on the VM (default vCPU/4)")
    p.add_argument("--max-minutes", type=float, default=90, help="hard stop: delete the VM after this long")
    p.add_argument("--list-plans", action="store_true")
    a = p.parse_args()
    if not os.environ.get("VULTR_API_KEY"):
        raise SystemExit("set VULTR_API_KEY in your shell first (never commit it)")

    if a.list_plans or not a.plan:
        for pl in plans(a.region, a.min_vcpu)[:10]:
            print(f"{pl['id']:28s} {pl['vcpu_count']:3d} vCPU {pl['ram'] // 1024:4d} GB  "
                  f"${pl['monthly_cost']}/mo (~${pl['monthly_cost'] / 730:.2f}/h)")
        if not a.plan:
            print("\nre-run with --plan <id>")
        return

    pl = next((x for x in plans(a.region, 1) if x["id"] == a.plan), None)
    if pl:
        print(f"{a.plan}: ~${pl['monthly_cost'] / 730:.2f}/h, at most ~${pl['monthly_cost'] / 730 * a.max_minutes / 60:.2f} "
              f"with --max-minutes {a.max_minutes:g}", flush=True)
    iid = call("POST", "/instances", {
        "region": a.region, "plan": a.plan, "os_id": ubuntu_os_id(),
        "sshkey_id": [ssh_key_id(a.pubkey)], "label": "duquantum-grid", "tags": ["duquantum"],
    })["instance"]["id"]
    print("created instance", iid, flush=True)
    t0 = time.time()
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
    finally:
        call("DELETE", f"/instances/{iid}")
        print(f"deleted instance {iid} after {(time.time() - t0) / 60:.1f} min "
              "(confirm at https://my.vultr.com/subs/)", flush=True)


if __name__ == "__main__":
    main()
