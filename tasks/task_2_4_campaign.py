"""Bounded, resumable Task 2.4 research jobs; see docs/task_2_4_README.md.

The scheduler imports no numerical library. Each isolated subprocess receives
CPU affinity and thread limits before importing its solver. A completed job is
execution evidence, not an assertion of convergence or scientific superiority.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results/task_2_4_campaign"


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def source_hashes():
    files = sorted(list((ROOT / "src").glob("*.py")) +
                   list((ROOT / "tasks").glob("*.py")))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}


def job(kind, parameters, purpose, priority=10):
    identity = json.dumps([kind, parameters], sort_keys=True).encode()
    return {"id": kind + "_" + hashlib.sha256(identity).hexdigest()[:16],
            "kind": kind, "parameters": parameters, "purpose": purpose,
            "priority": priority}


def prepare(output, preset="research"):
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists():
        raise FileExistsError("Manifest exists; use run to resume, or a new output directory")
    jobs = []
    if preset == "smoke":
        jobs.append(job("pulse", {"Na": 8, "Nb": 3, "alpha": .8, "ratio": .05,
                                  "duration": .08, "idle": .02, "step": .01},
                        "Small end-to-end execution smoke; not physical-target evidence", 0))
    else:
        # Tuned constant baselines share alpha, amplitude bounds, idle and clocks.
        for duration in (2., 4.):
            for ratio in (0., .05, .1, .25, .5):
                jobs.append(job("pulse", {"profile": "constant", "ratio": ratio,
                    "duration": duration, "Na": 24, "Nb": 8, "rtol": 1e-9,
                    "atol": 1e-11}, "Discovery: tuned constant and matched idle controls", 1))
            for profile in ("raised_cosine", "gaussian", "build_hold_deplete"):
                for ratio in (.1, .25, .5):
                    jobs.append(job("pulse", {"profile": profile, "ratio": ratio,
                        "duration": duration, "Na": 24, "Nb": 8,
                        "rtol": 1e-9, "atol": 1e-11},
                        "Discovery: fixed-alpha shape comparison at common duration", 2))
        for ratio in (.1, .25):
            jobs.append(job("pulse", {"profile": "constant", "ratio": ratio,
                "duration": 8., "Na": 24, "Nb": 8, "rtol": 1e-9, "atol": 1e-11},
                "Discovery: longer constant comparator for information/time trade-off", 2))
        for ratio in (.25, .5):
            for hold, tail in ((.4, -.2), (.7, -.6)):
                jobs.append(job("pulse", {"profile": "build_hold_deplete", "ratio": ratio,
                    "hold_ratio": hold, "tail_ratio": tail, "duration": 4.,
                    "Na": 24, "Nb": 8, "rtol": 1e-9, "atol": 1e-11},
                    "Discovery: bounded signed termination; no assumed improvement", 3))
        jobs.append(job("design", {"duration": 2., "seed": 2026},
                        "Cheap semiclassical candidate generation, then quantum testing", 0))
        for ratio in (0., .25, .5):
            for loss_off in (False, True):
                parameters = {"ratio": ratio, "Na": 32, "Nb": 12}
                if loss_off:
                    parameters["kappa_a"] = 0.
                jobs.append(job("dephasing", parameters,
                    "Even-cat coherence envelope separates deterministic Z rotation, leakage and physical memory loss", 3))
        for alpha in (1.2, 1.4, 2.1):
            for ratio in (0., .25, .5):
                jobs.append(job("spectrum", {"alpha": alpha, "ratio": ratio,
                    "Na": 16 if alpha < 2 else 32, "Nb": 6 if alpha < 2 else 12,
                    "k": 4, "time_check": False},
                    "Static candidate logical modes; retain overlaps and resolution limits", 1))
        for ratio in (0., .25):
            jobs.append(job("spectrum", {"alpha": 1.4, "ratio": ratio,
                "Na": 20, "Nb": 8, "k": 4},
                "Separate small-cat rate cutoff comparison", 4))
        for alpha in (1.2, 1.4):
            jobs.append(job("spectrum", {"alpha": alpha, "ratio": .25,
                "Na": 12, "Nb": 4, "k": 4, "time_check": True},
                "Matched small-cutoff time-domain/modal check; separate cutoff tests required", 2))
        jobs.append(job("spectrum", {"alpha": 2.1, "ratio": .25,
            "Na": 32, "Nb": 12, "k": 4, "shift": 1e-9},
            "Physical-target shift sensitivity; not a global dominance certificate", 4))
    # Remove exact duplicate cases; names depend on complete numerical settings.
    jobs = list({j["id"]: j for j in jobs}.values())
    manifest = {"created_utc": utc(), "preset": preset, "source_sha256": source_hashes(),
                "measurement_convention": "dY=2sqrt(eta*kappa)Re(exp(-i*phi)B)dt+dW; SNR_squared=4I",
                "purpose": "Executed evidence for Task 2.4(a-d); interpretation requires review",
                "jobs": sorted(jobs, key=lambda j: j["priority"])}
    atomic_json(output / "manifest.json", manifest)
    print(f"Prepared {len(jobs)} jobs in {output}")


def result_path(output, item):
    return output / "jobs" / item["id"]


def completed(output, item):
    path = result_path(output, item) / "summary.json"
    if not path.exists():
        return False
    value = json.loads(path.read_text())
    return value.get("execution_status") == "completed" and value.get("job") == item


def terminate(process):
    """Reap the whole solver process group, including the normal exit race."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def pulse_settings(item):
    return {key: value for key, value in item["parameters"].items()
            if key not in ("Na", "Nb", "rtol", "atol", "step")}


def expand_candidates(output, manifest):
    """Freeze finalists after discovery; reserve later jobs for their validation."""
    if manifest["preset"] == "smoke":
        return
    if not manifest.get("semiclassical_proposals_added"):
        design = next((j for j in manifest["jobs"] if j["kind"] == "design"), None)
        if design and completed(output, design):
            value = json.loads((result_path(output, design)/"summary.json").read_text())["metrics"]
            known = {j["id"] for j in manifest["jobs"]}
            for record in value["candidates"]:
                settings = dict(record["parameters"], Na=24, Nb=8, rtol=1e-9, atol=1e-11)
                proposal = job("pulse", settings,
                    "Quantum check of a semiclassical proposal; prediction alone is not evidence", 3)
                if proposal["id"] not in known:
                    manifest["jobs"].append(proposal)
                    known.add(proposal["id"])
            manifest["semiclassical_proposals_added"] = True
            atomic_json(output/"manifest.json", manifest)
    initial = [j for j in manifest["jobs"] if j["kind"] in ("pulse", "design")
               and j["priority"] < 5]
    if not initial or any(not (result_path(output, j)/"status.json").exists()
                          for j in initial):
        return
    states = [json.loads((result_path(output, j)/"status.json").read_text()) for j in initial]
    if any(s["status"] not in ("completed", "failed", "timeout") for s in states):
        return
    if manifest.get("finalists_frozen"):
        return
    candidates = []
    additions = []
    for item in initial:
        if not completed(output, item):
            continue
        value = json.loads((result_path(output, item)/"summary.json").read_text())["metrics"]
        if item["kind"] == "design":
            continue
        # A screen identifies candidates to validate, not accepted protocols.
        if (max(value["final_leakage"]) < .01 and
            max(value["final_wrong_population"]) < .01 and
            value["max_top2_a"] < 1e-3 and value["max_top_b"] < 1e-3 and
            value["max_trace_error"] < 1e-8 and value["final_min_eigenvalue"] > -1e-7):
            candidates.append((item, value))
    constants = [(j, m) for j, m in candidates if j["parameters"].get("profile") == "constant"
                 and j["parameters"].get("ratio", 0) > 0]
    shaped = [(j, m) for j, m in candidates if j["parameters"].get("profile") != "constant"]
    def score(pair):
        j, m = pair
        return m["information_at_pulse_end"] / m["cycle_duration_us"]
    selected = sorted(constants, key=score, reverse=True)[:1]
    selected += sorted(shaped, key=score, reverse=True)[:1]
    if shaped:
        information_floor = .25*max(m["information_at_pulse_end"] for _, m in shaped)
        useful = [(j, m) for j, m in shaped if m["information_at_pulse_end"] >= information_floor]
        depleted = min(useful, key=lambda pair: max(pair[1]["buffer_population_at_pulse_end"]))
        if depleted[0]["id"] not in {j["id"] for j, _ in selected}:
            selected.append(depleted)
    for item, _ in selected:
        p = pulse_settings(item)
        if p.get("profile", "constant") != "constant":
            for na, nb in ((32, 12), (40, 14)):
                additions.append(job("pulse", dict(p, profile="constant", Na=na, Nb=nb),
                    "Matched constant comparator: identical duration, peak drive and recovery", 6))
        for na, nb in ((32, 12), (40, 12), (32, 14), (40, 14)):
            additions.append(job("pulse", dict(p, Na=na, Nb=nb),
                "Finalist validation: memory, buffer and joint cutoff increases", 6))
        additions.append(job("pulse", dict(p, Na=32, Nb=12, step=.005,
                                            rtol=1e-11, atol=1e-13),
            "Finalist validation: time-grid and solver refinement", 7))
        for changes in ({"drive_scale": .95}, {"drive_scale": 1.05},
                        {"phase": -.05}, {"phase": .05}, {"order": "sine"},
                        {"circuit_correction": True},
                        {"coupling_scale": .95}, {"coupling_scale": 1.05},
                        {"buffer_loss_scale": .95}, {"buffer_loss_scale": 1.05},
                        {"kappa_a": 0.}):
            additions.append(job("pulse", dict(p, Na=32, Nb=12, **changes),
                "Finalist robustness / circuit / memory-loss control; matched idle included", 8))
    manifest["finalists_frozen"] = {"utc": utc(),
        "discovery_ids": [j["id"] for j, _ in selected],
        "selection": "Throughput baseline, shaped throughput and depleted shaped candidate above 25% information floor; final error/leakage <1%, then independent validation"}
    known = {j["id"] for j in manifest["jobs"]}
    for addition in additions:
        if addition["id"] not in known:
            manifest["jobs"].append(addition)
            known.add(addition["id"])
    manifest["jobs"].sort(key=lambda j: j["priority"])
    atomic_json(output / "manifest.json", manifest)


def worker(output, identifier, cpus):
    if cpus and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, set(map(int, cpus.split(","))))
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    os.environ["MPLBACKEND"] = "Agg"
    manifest = json.loads((output/"manifest.json").read_text())
    if manifest["source_sha256"] != source_hashes():
        raise RuntimeError("Source changed after manifest preparation; use a frozen source snapshot")
    item = next(j for j in manifest["jobs"] if j["id"] == identifier)
    folder = result_path(output, item)
    folder.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    atomic_json(folder/"status.json", {"status": "running", "started_utc": utc(),
                                       "pid": os.getpid(), "job": item})
    try:
        import numpy as np
        settings = dict(item["parameters"])
        arrays = {}
        if item["kind"] == "pulse":
            from src.readout_pulses import simulate_pulse, pulse_envelope
            from src import config as C
            if "coupling_scale" in settings:
                settings["g2"] = settings.pop("coupling_scale")*C.G2
                settings["control_g2"] = C.G2
            if "buffer_loss_scale" in settings:
                settings["kappa_b"] = settings.pop("buffer_loss_scale")*C.KAPPA_B
            t, e, metrics = simulate_pulse(**settings)
            arrays = {"t": t, "expects": e,
                "envelope": pulse_envelope(t, settings["duration"],
                    settings.get("profile", "constant"), settings.get("edge_fraction", .1),
                    settings.get("hold_ratio", .7), settings.get("tail_ratio", -.2),
                    settings.get("knots", (.2, .8)))}
        elif item["kind"] == "spectrum":
            from src.readout_campaign_spectrum import analyze_spectrum
            metrics, arrays = analyze_spectrum(**settings)
        elif item["kind"] == "design":
            from src.readout_semiclassical import design_candidates
            metrics = {"candidates": design_candidates(**settings,
                output_path=folder/"semiclassical_search.json"),
                "interpretation": "Candidate generator only; requires full quantum verification"}
        elif item["kind"] == "dephasing":
            from src.readout_dephasing import simulate_dephasing
            metrics, arrays = simulate_dephasing(**settings)
        else:
            raise ValueError(f"Unknown job kind {item['kind']}")
        if arrays:
            temporary = folder/"trajectories.tmp.npz"
            np.savez_compressed(temporary, **arrays)
            temporary.replace(folder/"trajectories.npz")
        result = {"execution_status": "completed", "job": item, "metrics": metrics,
                  "finished_utc": utc(), "worker_wall_s": time.monotonic()-started}
        atomic_json(folder/"summary.json", result)
        atomic_json(folder/"status.json", {"status": "completed", "finished_utc": utc(),
                                           "wall_s": time.monotonic()-started})
    except Exception:
        atomic_json(folder/"status.json", {"status": "failed", "finished_utc": utc(),
                    "error": traceback.format_exc(), "wall_s": time.monotonic()-started})
        raise


def run(output, workers=7, spectral_workers=1, cpus_per_worker=2, hours=3., job_timeout=1200):
    manifest = json.loads((output/"manifest.json").read_text())
    if manifest["source_sha256"] != source_hashes():
        raise RuntimeError("Run from the frozen source used to prepare the manifest")
    if min(workers, spectral_workers, cpus_per_worker, hours, job_timeout) <= 0:
        raise ValueError("Worker counts and deadlines must be positive")
    import fcntl
    lock = (output/"scheduler.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cpus = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else list(range(os.cpu_count() or 1))
    workers = min(workers, max(1, len(cpus)//cpus_per_worker))
    active, attempted, quit_requested = {}, set(), [False]
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: quit_requested.__setitem__(0, True))
    started, deadline = time.monotonic(), time.monotonic()+hours*3600
    events = (output/"events.jsonl").open("a", buffering=1)
    def event(**data):
        events.write(json.dumps(dict(utc=utc(), **data)) + "\n")
    event(event="scheduler_started", pid=os.getpid(), workers=workers, hours=hours)
    try:
        while True:
            expand_candidates(output, manifest)
            for slot, running in list(active.items()):
                process, item, launched, log = running
                expired = (time.monotonic()-launched > job_timeout or
                           time.monotonic() >= deadline or quit_requested[0])
                if process.poll() is None and expired:
                    terminate(process)
                    atomic_json(result_path(output, item)/"status.json",
                        {"status": "timeout", "finished_utc": utc(), "reason": "case or campaign deadline"})
                if process.poll() is not None:
                    log.close()
                    statefile = result_path(output, item)/"status.json"
                    state = json.loads(statefile.read_text()).get("status") if statefile.exists() else None
                    if state not in ("failed", "timeout") and not completed(output, item):
                        atomic_json(result_path(output, item)/"status.json",
                            {"status": "failed", "returncode": process.returncode, "finished_utc": utc()})
                    event(event="job_finished", id=item["id"], returncode=process.returncode)
                    del active[slot]
            pending = [j for j in manifest["jobs"] if j["id"] not in attempted
                       and not completed(output, j)]
            stopping = quit_requested[0] or time.monotonic() >= deadline or (output/"STOP").exists()
            spectral_active = sum(v[1]["kind"] == "spectrum" for v in active.values())
            if not stopping:
                for slot in range(workers):
                    if slot in active:
                        continue
                    item = next((j for j in pending if j["kind"] != "spectrum"
                                 or spectral_active < spectral_workers), None)
                    if item is None:
                        break
                    pending.remove(item)
                    folder = result_path(output, item)
                    folder.mkdir(parents=True, exist_ok=True)
                    atomic_json(folder/"status.json", {"status": "starting", "utc": utc()})
                    log = (folder/"worker.log").open("a")
                    group = cpus[slot*cpus_per_worker:(slot+1)*cpus_per_worker]
                    command = [sys.executable, "-u", "-m", "tasks.task_2_4_campaign", "worker",
                               "--output", str(output), "--id", item["id"],
                               "--cpus", ",".join(map(str, group))]
                    process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                               start_new_session=True)
                    active[slot] = process, item, time.monotonic(), log
                    attempted.add(item["id"])
                    spectral_active += item["kind"] == "spectrum"
                    event(event="job_started", id=item["id"], pid=process.pid, cpus=group)
            counts = Counter("completed" if completed(output, j) else
                (json.loads((result_path(output,j)/"status.json").read_text())["status"]
                 if (result_path(output,j)/"status.json").exists() else "queued") for j in manifest["jobs"])
            atomic_json(output/"status.json", {"updated_utc": utc(), "hostname": socket.gethostname(),
                "pid": os.getpid(), "scheduler": "running" if active or pending else "finished",
                "counts": dict(counts), "elapsed_s": time.monotonic()-started,
                "remaining_budget_s": max(0, deadline-time.monotonic()),
                "active": [{"id": value[1]["id"], "pid": value[0].pid} for value in active.values()]})
            if not active and (not pending or stopping):
                break
            time.sleep(2)
    finally:
        for process, item, _, log in active.values():
            if process.poll() is None:
                terminate(process)
                atomic_json(result_path(output, item)/"status.json",
                    {"status": "interrupted", "finished_utc": utc(),
                     "reason": "scheduler exited; no orphan workers retained"})
            log.close()
        events.close()
        status = json.loads((output/"status.json").read_text()) if (output/"status.json").exists() else {}
        counts = Counter("completed" if completed(output, j) else
            (json.loads((result_path(output,j)/"status.json").read_text())["status"]
             if (result_path(output,j)/"status.json").exists() else "queued") for j in manifest["jobs"])
        status.update(updated_utc=utc(), active=[], counts=dict(counts),
            scheduler="completed" if counts.get("completed", 0) == len(manifest["jobs"]) else "stopped_with_incomplete_cases")
        atomic_json(output/"status.json", status)
        # The scheduler's deadline stops jobs; it does not delete a billed VM.
        atomic_json(output/"scheduler_exit.json", {"finished_utc": utc(),
                    "elapsed_s": time.monotonic()-started, "incomplete_cases_retained": True})
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "status", "worker"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preset", choices=("smoke", "research"), default="research")
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--spectral-workers", type=int, default=1)
    parser.add_argument("--cpus-per-worker", type=int, default=2)
    parser.add_argument("--hours", type=float, default=3.)
    parser.add_argument("--job-timeout", type=float, default=1200)
    parser.add_argument("--id")
    parser.add_argument("--cpus", default="")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.command == "prepare":
        prepare(output, args.preset)
    elif args.command == "run":
        run(output, args.workers, args.spectral_workers, args.cpus_per_worker,
            args.hours, args.job_timeout)
    elif args.command == "worker":
        worker(output, args.id, args.cpus)
    else:
        for name in ("status.json", "scheduler_exit.json"):
            if (output/name).exists():
                print(name, (output/name).read_text())


if __name__ == "__main__":
    main()
