"""Collect an authorized research run without storing credentials in the repo."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import time


def collect(host, control_path, destination, hours=3.5, interval=60):
    destination.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+hours*3600
    ssh = shlex.join(["ssh", "-S", str(control_path), "-o", "BatchMode=yes",
                      "-o", "ConnectTimeout=10"])
    source = host+":/opt/duquantum/task24/results/task_2_4_campaign/"
    with (destination/"collection.log").open("a", buffering=1) as log:
        while time.monotonic() < deadline:
            try:
                result = subprocess.run(["rsync", "-az", "--partial", "--timeout=30",
                    "-e", ssh, source, str(destination)+"/"], capture_output=True,
                    text=True, timeout=50)
                record = {"utc": datetime.now(timezone.utc).isoformat(),
                          "rsync_exit": result.returncode}
                if result.returncode:
                    record["error"] = result.stderr[-800:]
                log.write(json.dumps(record)+"\n")
                marker = destination/"report_done.json"
                if result.returncode == 0 and marker.exists():
                    log.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
                        "collection": "final_outputs_downloaded", "report": json.loads(marker.read_text())})+"\n")
                    return
            except subprocess.TimeoutExpired:
                log.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
                                      "error": "bounded transfer timed out"})+"\n")
            time.sleep(min(interval, max(0, deadline-time.monotonic())))
        log.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
            "collection": "deadline_reached; downloaded evidence retained; remote run not assumed complete"})+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--control-path", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=3.5)
    parser.add_argument("--interval", type=float, default=60)
    args = parser.parse_args()
    if args.hours <= 0 or args.interval <= 0 or args.host.startswith("-") or ":" in args.host:
        parser.error("Expected a host, positive collection deadline and positive interval")
    collect(args.host, args.control_path, args.destination, args.hours, args.interval)
