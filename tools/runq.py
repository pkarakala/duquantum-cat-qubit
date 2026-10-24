"""File-based job queue for long production runs (CONTRACT §12). Stdlib only.

Keeps the laptop inside its limits: at most --max-jobs jobs and --max-ram-gb of declared RAM at once,
and only one "big" job (ram_gb > 3, i.e. a large sparse LU) at a time. Failed jobs are never retried.

    python -m tools.runq submit --name <job> --ram-gb <float> [--cwd <path>] -- <command ...>
    python -m tools.runq worker [--max-jobs 3] [--max-ram-gb 11] [--once] [--force]
    python -m tools.runq status
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BIG_GB = 3.0
XLA = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
NAME_RE = r"^[A-Za-z0-9_.\-]+$"


def queue_dir() -> Path:
    return Path(os.environ.get("DUQ_RUNQ_DIR") or "results/logs/runq")


def _iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _save(job):
    """Atomic write of a job file (tmp + os.replace, retried for Windows sharing violations)."""
    path = Path(job["_file"])
    data = json.dumps({k: v for k, v in job.items() if not k.startswith("_")}, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    for attempt in range(5):
        try:
            os.replace(tmp, path)
            return
        except OSError:
            time.sleep(0.1)
    path.write_text(data, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def load_jobs(root) -> list[dict]:
    """All jobs, oldest first (filenames start with the UTC submit time)."""
    jobs = []
    for p in sorted((Path(root) / "jobs").glob("*.json")):
        try:
            job = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"runq: skipping unreadable {p.name} ({e})", file=sys.stderr)
            continue
        job["_file"] = str(p)
        jobs.append(job)
    return jobs


def submit(root, name, ram_gb, cmd: list[str], cwd=None) -> Path:
    """Queue one job as pending; returns its JSON path. ValueError on a bad or duplicate name, ram, or cmd."""
    root = Path(root).resolve()
    if not isinstance(name, str) or not re.match(NAME_RE, name):
        raise ValueError(f"bad job name {name!r} (allowed: {NAME_RE})")
    if not ram_gb > 0:
        raise ValueError(f"ram_gb must be > 0, got {ram_gb!r}")
    if not cmd:
        raise ValueError("empty command")
    if any(j.get("name") == name for j in load_jobs(root)):
        raise ValueError(f"a job named {name!r} already exists (names are unique; logs are <name>.log)")
    (root / "jobs").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    path = root / "jobs" / f"{stamp}_{name}.json"
    job = {"name": name, "cmd": [str(c) for c in cmd], "cwd": str(Path(cwd or os.getcwd()).resolve()),
           "ram_gb": float(ram_gb), "state": "pending", "submitted_at": _iso_now(), "started_at": None,
           "ended_at": None, "t_start": None, "t_end": None, "pid": None, "exit_code": None, "wall_s": None,
           "log": str(root / "logs" / f"{name}.log"), "reason": None, "_file": str(path)}
    _save(job)
    return path


def _start(job):
    """Launch one job with the two-thread XLA setting; returns the Popen or None if it could not start."""
    env = {**os.environ, "XLA_FLAGS": XLA, "PYTHONUNBUFFERED": "1"}
    Path(job["log"]).parent.mkdir(parents=True, exist_ok=True)
    job.update(state="running", started_at=_iso_now(), t_start=time.time())
    try:
        with open(job["log"], "ab") as log:
            proc = subprocess.Popen(job["cmd"], cwd=job["cwd"], env=env, stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    except OSError as e:
        t_end = time.time()
        job.update(state="failed", reason=f"could not start: {e}", ended_at=_iso_now(), t_end=t_end,
                   wall_s=t_end - job["t_start"])
        _save(job)
        print(f"runq: {job['name']} failed to start ({e})")
        return None
    job["pid"] = proc.pid
    _save(job)
    print(f"runq: started {job['name']} (pid {proc.pid}, {job['ram_gb']:g} GB)")
    return proc


def _finish(job, rc):
    t_end = time.time()
    job.update(state="done" if rc == 0 else "failed", exit_code=rc, ended_at=_iso_now(), t_end=t_end,
               wall_s=t_end - job["t_start"])
    if rc != 0:
        job["reason"] = f"exit code {rc}"
    _save(job)
    print(f"runq: {job['name']} {job['state']} (exit {rc}, {job['wall_s']:.1f} s)")


def worker(root, max_jobs=3, max_ram_gb=11.0, poll_s=2.0, once=False, force=False) -> int:
    """Run pending jobs FIFO within the limits. Returns 2 if another worker holds the lock.
    With once=True, returns when nothing runnable is left (0 if the queue is empty, 1 if some pending
    job can never fit these limits)."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "worker.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if not force:
            print(f"runq: {lock} exists: another worker is running (use --force if it is stale)", file=sys.stderr)
            return 2
        fd = os.open(lock, os.O_CREAT | os.O_TRUNC | os.O_WRONLY)
    os.write(fd, f"{os.getpid()} {_iso_now()}\n".encode())
    os.close(fd)
    running = {}   # name -> (proc, job)
    warned = set()
    try:
        for job in load_jobs(root):
            if job.get("state") == "running":
                job.update(state="failed", reason="orphaned (worker restarted)", ended_at=_iso_now())
                _save(job)
                print(f"runq: {job['name']} was running under a previous worker: marked failed")
        while True:
            for name, (proc, job) in list(running.items()):
                rc = proc.poll()
                if rc is not None:
                    _finish(job, rc)
                    del running[name]
            pending = [j for j in load_jobs(root) if j.get("state") == "pending" and j["name"] not in running]
            unfit = []
            for job in pending:
                ram, big = job["ram_gb"], job["ram_gb"] > BIG_GB
                if ram > max_ram_gb:
                    unfit.append(job)
                    if job["name"] not in warned:
                        warned.add(job["name"])
                        print(f"runq: {job['name']} needs {ram:g} GB > --max-ram-gb {max_ram_gb:g}: left pending")
                    continue
                used = sum(j["ram_gb"] for _, j in running.values())
                big_running = any(j["ram_gb"] > BIG_GB for _, j in running.values())
                if len(running) < max_jobs and used + ram <= max_ram_gb and not (big and big_running):
                    proc = _start(job)
                    if proc is not None:
                        running[job["name"]] = (proc, job)
            if once and not running and len(pending) == len(unfit):
                return 1 if unfit else 0
            time.sleep(poll_s)
    finally:
        lock.unlink(missing_ok=True)


def status_table(root) -> str:
    head = ("name", "state", "ram_gb", "exit", "wall_s", "log")
    rows = [(j.get("name", "?"), j.get("state", "?"), f"{j.get('ram_gb', 0):g}",
             "" if j.get("exit_code") is None else str(j["exit_code"]),
             "" if j.get("wall_s") is None else f"{j['wall_s']:.1f}", j.get("log", ""))
            for j in load_jobs(root)]
    widths = [max(len(r[i]) for r in [head] + rows) for i in range(len(head))]
    lines = [" | ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in [head] + rows]
    lines.insert(1, "-+-".join("-" * w for w in widths))
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="File-based job queue (CONTRACT §12).")
    sub = p.add_subparsers(dest="action", required=True)
    s = sub.add_parser("submit", help="queue a job")
    s.add_argument("--name", required=True)
    s.add_argument("--ram-gb", type=float, required=True)
    s.add_argument("--cwd", default=None)
    s.add_argument("cmd", nargs=argparse.REMAINDER)
    w = sub.add_parser("worker", help="run queued jobs")
    w.add_argument("--max-jobs", type=int, default=3)
    w.add_argument("--max-ram-gb", type=float, default=11.0)
    w.add_argument("--poll-s", type=float, default=2.0)
    w.add_argument("--once", action="store_true", help="exit when nothing is pending or running")
    w.add_argument("--force", action="store_true", help="ignore an existing worker.lock")
    sub.add_parser("status", help="print the job table")
    args = p.parse_args(argv)
    root = queue_dir()

    if args.action == "submit":
        # PowerShell 5.1 may swallow "--", so accept the command with or without it.
        cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
        try:
            path = submit(root, args.name, args.ram_gb, cmd, cwd=args.cwd)
        except ValueError as e:
            print(f"runq submit: {e}", file=sys.stderr)
            return 1
        print(f"queued {args.name} -> {path}")
        return 0
    if args.action == "worker":
        try:
            return worker(root, args.max_jobs, args.max_ram_gb, args.poll_s, args.once, args.force)
        except KeyboardInterrupt:
            print("runq: worker interrupted; jobs still marked running become 'orphaned' at the next start")
            return 130
    print(status_table(root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
