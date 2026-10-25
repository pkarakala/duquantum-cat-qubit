"""Cost and RAM profile of the sparse Liouvillian eigen-solver.

Each truncation runs in a fresh child so a wall-time or memory overrun can be killed
without losing the cases that already finished. Records are wall time at one truncation,
not a converged Gamma_X (L2b owns those). Hold $MAIN/.git/duq-heavy.lock around any
run expected to exceed 1.5 GB: this machine's in-lane cap is 3 GB, and anything
estimated above 4 GB stays queued.
"""
import argparse
import ctypes
import json
import os
import resource
import signal
import subprocess
import sys
import threading
import time
import traceback

# Thread caps before numpy/scipy/jax load in the child. The parent stays import-light
# until every child has exited, so a 28x8 factorization is not added to a second JAX.
for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "2")
os.environ.setdefault("MPLBACKEND", "Agg")

# Apple's rusage_info_v4: uuid[16], then user, system, idle wakeups, interrupt wakeups,
# pageins, wired, resident, phys_footprint. RSS under-counts compressed pages on macOS;
# phys_footprint is the number that filled RAM on the killed MMD factorization.
_LIBPROC = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
_LIBPROC.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
_LIBPROC.proc_pid_rusage.restype = ctypes.c_int
_RUSAGE_INFO_V4 = 4

MODEL_FULL_S = 113.0     # RESEARCH §9: full L at Na*Nb^2 = 1792
MODEL_X = 1792.0
GIB = 1024.0 ** 3
PERMC_DEFAULT = "COLAMD"
SCRIPT = "tasks/task_spectral_profile.py"


def _footprint_bytes(pid):
    """Current phys_footprint (bytes), or 0 if libproc refuses the pid.

    The buffer is larger than rusage_info_v4: a short one lets the kernel write past
    the end and SIGSEGV the caller. Index 9 is phys_footprint (resident size is index 8).
    """
    buf = (ctypes.c_uint64 * 64)()
    if _LIBPROC.proc_pid_rusage(int(pid), _RUSAGE_INFO_V4, ctypes.byref(buf)) != 0:
        return 0
    return int(buf[9])


def _ru_maxrss_bytes():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024)


def _model_seconds(na, nb, sector):
    """RESEARCH §9 full-L time, divided by 8 for the odd block."""
    t = MODEL_FULL_S * ((na * nb * nb) / MODEL_X) ** 3
    return t / 8.0 if sector == "odd" else t


def _parse_size(text):
    na, nb = text.lower().split("x")
    return int(na), int(nb)


def _record_id(alpha, na, nb, sector):
    tag = f"a{alpha:.2f}.na{na}nb{nb}"
    kind = "eig" if sector == "odd" else "eig_full"
    return f"t2_1.wall_s.{kind}.two_mode.{tag}"


def _solve(na, nb, alpha, sector, permc):
    """One factorization. Odd COLAMD goes through gamma_x; other orderings use the same LU helper."""
    from src import config as C  # sets double precision before any operator is built

    import numpy as np

    from src import spectral
    from src.model import two_mode

    H, jumps, _ = two_mode(na, nb, C.G2, alpha ** 2 * C.G2, C.KAPPA_B, C.KAPPA_A)
    if sector == "odd" and permc == spectral.PERMC:
        out = spectral.gamma_x(H, jumps, na, nb)
        return {
            "gamma_x": out["gamma_x"], "rel_residual": out["rel_residual"],
            "edge_weight": out["edge_weight"], "cond_est": out["cond_est"],
            "wall_s": out["wall_s"], "build_s": out["build_s"], "lu_s": out["lu_s"],
            "eigs_s": out["eigs_s"], "lu_nnz": out["lu_nnz"], "nnz": out["nnz"],
            "dim": out["dim"], "sector": "odd", "sigma": out["sigma"], "k": out["k"],
        }

    t0 = time.perf_counter()
    L = spectral.liouvillian(H, jumps)
    build_s = time.perf_counter() - t0
    if sector == "odd":
        spectral._require_memory_loss(jumps, na, nb)
        idx = spectral.sector_indices(na, nb, 1)
        A = spectral._block(L, idx)
        sigma, k = 0.0, 2
    elif sector == "full":
        # Undeflated full L is singular at 0, so shift-invert at a small positive sigma.
        idx = None
        A = L
        sigma, k = 1e-3, 3
    else:
        raise ValueError(f"sector must be 'odd' or 'full', got {sector!r}")
    si = spectral._shift_invert(A, k, sigma, left=True, permc=permc)
    n = L.shape[0]
    best = None
    odd = spectral.sector_indices(na, nb, 1)
    for m, lam in enumerate(si["lams"]):
        v = si["V"][:, m]
        if idx is None:
            v_full, w_full = v, si["W"][:, m]
        else:
            v_full = spectral._embed(v, idx, n)
            w_full = spectral._embed(si["W"][:, m], idx, n)
        frac = float(np.vdot(v_full[odd], v_full[odd]).real / np.vdot(v_full, v_full).real)
        if sector == "full" and frac <= 0.99:
            continue
        if best is None or abs(lam) < abs(best[0]):
            best = (lam, v_full, w_full, frac)
    if best is None:
        raise RuntimeError("no mode with >99% of its weight on the odd sector")
    lam, v_full, w_full, frac = best
    d = spectral.diagnostics(L, lam, v_full, na, nb, w_full)
    return {
        "gamma_x": float(-lam.real), **d,
        "wall_s": time.perf_counter() - t0, "build_s": build_s,
        "lu_s": si["lu_s"], "eigs_s": si["eigs_s"], "lu_nnz": si["lu_nnz"],
        "nnz": int(A.nnz), "dim": int(A.shape[0]), "sector": sector,
        "sigma": sigma, "k": k, "odd_weight": frac,
    }


def _run_single(args):
    na, nb = _parse_size(args.single)
    stop = threading.Event()
    peak = [0]

    def _sample():
        while True:
            peak[0] = max(peak[0], _footprint_bytes(os.getpid()))
            if stop.wait(0.2):
                break

    sampler = threading.Thread(target=_sample, daemon=True)
    sampler.start()
    try:
        out = _solve(na, nb, args.alpha, args.sector, args.permc or PERMC_DEFAULT)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    finally:
        stop.set()
        peak[0] = max(peak[0], _footprint_bytes(os.getpid()))
        sampler.join(timeout=1.0)
    out["peak_footprint_bytes"] = peak[0]
    out["ru_maxrss_bytes"] = _ru_maxrss_bytes()
    out["permc"] = args.permc or PERMC_DEFAULT
    print("RESULT " + json.dumps(out), flush=True)


def _child_env():
    env = os.environ.copy()
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[var] = "2"
    env.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2")
    return env


def _rss_bytes(pid):
    try:
        import psutil
        return int(psutil.Process(pid).memory_info().rss)
    except Exception:
        return 0


def _run_child(na, nb, alpha, sector, permc, max_wall, max_rss_gb):
    """Spawn one case. status: 0 ok, 1 timeout, 2 ram, 3 the child died without a RESULT line."""
    cmd = [
        sys.executable, "-m", "tasks.task_spectral_profile",
        "--single", f"{na}x{nb}", "--sector", sector, "--alpha", str(alpha), "--permc", permc,
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=_child_env(),
        start_new_session=True, cwd=os.getcwd(),
    )
    lines = []

    def _read():
        for raw in proc.stdout:
            lines.append(raw.decode(errors="replace"))

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()
    t0 = time.perf_counter()
    polled = 0
    status = 0
    while proc.poll() is None:
        polled = max(polled, _footprint_bytes(proc.pid), _rss_bytes(proc.pid))
        elapsed = time.perf_counter() - t0
        if elapsed > max_wall or polled > max_rss_gb * GIB:
            status = 1 if elapsed > max_wall else 2
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            break
        time.sleep(0.5)
    proc.wait()
    reader.join(timeout=5)
    elapsed = time.perf_counter() - t0
    text = "".join(lines)
    result = None
    for line in reversed(text.splitlines()):
        if line.startswith("RESULT "):
            result = json.loads(line[len("RESULT "):])
            break
    if status == 0 and result is None:
        status = 3
        sys.stderr.write(text[-4000:])
    peak = polled
    if result is not None:
        peak = max(peak, int(result.get("peak_footprint_bytes") or 0), int(result.get("ru_maxrss_bytes") or 0))
    row = {
        "na": na, "nb": nb, "sector": sector, "permc": permc, "status": status,
        "proc_wall_s": elapsed, "peak_rss_gb": peak / GIB, "log_tail": "" if result else text[-1500:],
    }
    if result is not None and status == 0:
        row.update({k: result[k] for k in (
            "gamma_x", "rel_residual", "edge_weight", "cond_est", "wall_s", "build_s",
            "lu_s", "eigs_s", "lu_nnz", "nnz", "dim", "sigma", "k")})
        if "odd_weight" in result:
            row["odd_weight"] = result["odd_weight"]
    return row


def _cases(args):
    if args.quick:
        return 1.0, [
            (12, 4, "odd", PERMC_DEFAULT),
            (16, 4, "odd", PERMC_DEFAULT),
            (20, 6, "odd", PERMC_DEFAULT),
            (12, 4, "full", PERMC_DEFAULT),
        ], []
    sizes = [_parse_size(s) for s in args.sizes.split(",") if s.strip()]
    if args.extra and (32, 12) not in sizes:
        sizes.append((32, 12))
    main = [(na, nb, "odd", PERMC_DEFAULT) for na, nb in sizes]
    if not args.no_full and (28, 8) in [(na, nb) for na, nb in sizes]:
        main.append((28, 8, "full", PERMC_DEFAULT))
    main.sort(key=lambda c: (c[0] * c[1] * c[1], 0 if c[2] == "odd" else 1))
    compare = [(28, 8, "odd", "MMD_AT_PLUS_A")] if args.permc_compare else []
    return args.alpha, main, compare


def _blank(na, nb, sector, permc, status):
    return {
        "na": na, "nb": nb, "sector": sector, "permc": permc, "status": status,
        "dim": 0, "nnz": 0, "lu_nnz": 0, "wall_s": float("nan"), "lu_s": float("nan"),
        "eigs_s": float("nan"), "peak_rss_gb": float("nan"), "gamma_x": float("nan"),
        "rel_residual": float("nan"), "edge_weight": float("nan"),
    }


def _run_list(cases, alpha, max_wall, max_rss_gb, skip_larger):
    rows = []
    failed_x = None
    fail_status = 2
    for na, nb, sector, permc in cases:
        x = na * nb * nb
        if skip_larger and failed_x is not None and x > failed_x:
            print(f"SKIP {na}x{nb} {sector} (larger than a case that hit status {fail_status})", flush=True)
            rows.append(_blank(na, nb, sector, permc, fail_status))
            continue
        print(f"RUN {na}x{nb} {sector} permc={permc} alpha={alpha}", flush=True)
        row = _run_child(na, nb, alpha, sector, permc, max_wall, max_rss_gb)
        rows.append(row)
        g = row.get("gamma_x")
        print(
            f"DONE {na}x{nb} {sector} status={row['status']} wall={row.get('wall_s')} "
            f"proc_wall={row['proc_wall_s']:.1f}s footprint_gb={row['peak_rss_gb']:.3f} "
            f"gamma={g} edge={row.get('edge_weight')} resid={row.get('rel_residual')}",
            flush=True,
        )
        if skip_larger and row["status"] in (1, 2) and (failed_x is None or x < failed_x):
            failed_x = x
            fail_status = row["status"]
    return rows


def _plot(rows, alpha, quick):
    import matplotlib.pyplot as plt
    import numpy as np

    from src.plotting import save as save_fig

    ok = [r for r in rows if r["status"] == 0 and r["permc"] == PERMC_DEFAULT]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    xs = np.array([r["na"] * r["nb"] ** 2 for r in ok], dtype=float)
    if xs.size:
        grid = np.logspace(np.log10(xs.min() * 0.8), np.log10(max(xs.max(), MODEL_X) * 1.2), 40)
        ax[0].plot(grid, MODEL_FULL_S * (grid / MODEL_X) ** 3, "k--", lw=1, label=r"113 s $(x/1792)^3$")
        ax[0].plot(grid, MODEL_FULL_S * (grid / MODEL_X) ** 3 / 8, "k:", lw=1, label="odd model (/8)")
    for sector, marker, label in (("odd", "o", "odd block"), ("full", "s", "full L")):
        sel = [r for r in ok if r["sector"] == sector]
        if not sel:
            continue
        x = [r["na"] * r["nb"] ** 2 for r in sel]
        ax[0].plot(x, [r["wall_s"] for r in sel], marker, label=label)
        ax[1].plot(x, [r["peak_rss_gb"] for r in sel], marker, label=label)
    ax[0].set_xscale("log")
    ax[0].set_yscale("log")
    ax[0].set_xlabel(r"$N_a N_b^{2}$")
    ax[0].set_ylabel("wall time (s)")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3, which="both")
    ax[1].set_xscale("log")
    ax[1].set_xlabel(r"$N_a N_b^{2}$")
    ax[1].set_ylabel("peak footprint (GiB)")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3)
    fig.suptitle(f"Task 2.1 spectral cost, alpha={alpha:g}, {PERMC_DEFAULT}")
    save_fig(fig, "task_2_1_spectral_cost", quick=quick)
    plt.close(fig)


def _fit_exponent(rows):
    import numpy as np

    pts = [(r["na"] * r["nb"] ** 2, r["wall_s"]) for r in rows
           if r["status"] == 0 and r["sector"] == "odd" and r["permc"] == PERMC_DEFAULT and r["wall_s"] > 0]
    if len(pts) < 2:
        return None
    slope = np.polyfit(np.log([p[0] for p in pts]), np.log([p[1] for p in pts]), 1)[0]
    return float(slope)


def _record_rows(rows, alpha, quick):
    import numpy as np

    from src.results import record, save_arrays, std_params

    params = std_params(alpha=alpha)
    for r in rows:
        if r["status"] != 0 or r["permc"] != PERMC_DEFAULT:
            continue
        t_model = _model_seconds(r["na"], r["nb"], r["sector"])
        rel = abs(r["wall_s"] - t_model) / t_model
        notes = ("cost profile; wall time is a property of this truncation, not a converged "
                 "physics quantity, so convergence is null. peak_rss_gb is macOS phys_footprint "
                 f"in GiB. Ordering {PERMC_DEFAULT}.")
        if r["sector"] == "odd" and r["edge_weight"] >= 1e-6:
            notes += " edge_weight >= 1e-6 flags a truncation artifact; gamma_x is not a converged rate."
        numerics = {
            "rel_residual": r["rel_residual"], "edge_weight": r["edge_weight"],
            "cond_est": r["cond_est"], "sector": r["sector"], "sigma": r["sigma"], "k": r["k"],
            "dim": r["dim"], "nnz": r["nnz"], "lu_nnz": r["lu_nnz"], "build_s": r["build_s"],
            "lu_s": r["lu_s"], "eigs_s": r["eigs_s"], "peak_rss_gb": r["peak_rss_gb"],
            "gamma_x": r["gamma_x"], "blas_threads": 2, "permc": r["permc"],
            "proc_wall_s": r["proc_wall_s"],
        }
        if "odd_weight" in r:
            numerics["odd_weight"] = r["odd_weight"]
        rid = _record_id(alpha, r["na"], r["nb"], r["sector"])
        record(
            rid, task="2.1", quantity="wall_s", value=r["wall_s"], units="s",
            method=("liouvillian_eig_odd_sector" if r["sector"] == "odd"
                    else "liouvillian_eig_full_small_sigma"),
            params=params, script=SCRIPT, truncation={"Na": r["na"], "Nb": r["nb"]},
            convergence=None, numerics=numerics, wall_s=r["wall_s"], notes=notes, quick=quick,
            cross_check=[{
                "method": "cost_model", "ref_id": None, "value": t_model,
                "rel_diff": rel, "tol": 1.0, "agree": bool(rel <= 1.0),
            }],
            artifacts={
                "figure": ("figures/quick/" if quick else "figures/") + "task_2_1_spectral_cost.png",
                "arrays": ("results/quick/arrays/" if quick else "results/arrays/")
                          + f"t2_1.wall_s.eig.two_mode.a{alpha:.2f}.profile.npz",
            },
        )
    recorded = [r for r in rows if r["permc"] == PERMC_DEFAULT]

    def col_float(key):
        vals = []
        for r in recorded:
            v = r.get(key)
            vals.append(np.nan if v is None else float(v))
        return np.asarray(vals, dtype=float)

    def col_int(key):
        vals = []
        for r in recorded:
            v = r.get(key)
            vals.append(0 if v is None or (isinstance(v, float) and np.isnan(v)) else int(v))
        return np.asarray(vals, dtype=int)

    save_arrays(
        f"t2_1.wall_s.eig.two_mode.a{alpha:.2f}.profile", quick=quick,
        na=col_int("na"), nb=col_int("nb"),
        sector=np.array([0 if r["sector"] == "odd" else 1 for r in recorded], dtype=int),
        dim=col_int("dim"), nnz=col_int("nnz"), lu_nnz=col_int("lu_nnz"),
        wall_s=col_float("wall_s"), lu_s=col_float("lu_s"), eigs_s=col_float("eigs_s"),
        peak_rss_gb=col_float("peak_rss_gb"), gamma_x=col_float("gamma_x"),
        rel_residual=col_float("rel_residual"), edge_weight=col_float("edge_weight"),
        status=col_int("status"),
    )


def main(argv=None):
    p = argparse.ArgumentParser(description="Spectral cost profile (Task 2.1).")
    p.add_argument("--quick", action="store_true", help="alpha=1, odd 12x4, 16x4, 20x6 and full 12x4")
    p.add_argument("--sizes", default="24x10,28x8,32x10,40x8,48x8")
    p.add_argument("--extra", action="store_true", help="also run 32x12")
    p.add_argument("--alpha", type=float, default=2.1)
    p.add_argument("--no-full", action="store_true")
    p.add_argument("--permc-compare", action="store_true")
    p.add_argument("--max-wall", type=float, default=600.0)
    # 6 GB is the brief's 16 GB-laptop kill line. This machine has 8 GB; the runbook
    # caps an in-lane process at 3 GB and the coordinator queues anything above 4 GB.
    p.add_argument("--max-rss-gb", type=float, default=4.0)
    p.add_argument("--single", default=None, help=argparse.SUPPRESS)
    p.add_argument("--sector", default="odd", choices=("odd", "full"))
    p.add_argument("--permc", default=None)
    args = p.parse_args(argv)
    if args.single:
        _run_single(args)
        return 0
    alpha, main_cases, compare = _cases(args)
    rows = _run_list(main_cases, alpha, args.max_wall, args.max_rss_gb, skip_larger=True)
    if compare:
        rows.extend(_run_list(compare, alpha, args.max_wall, args.max_rss_gb, skip_larger=False))
    _plot([r for r in rows if r["permc"] == PERMC_DEFAULT], alpha, args.quick)
    _record_rows(rows, alpha, args.quick)
    p_fit = _fit_exponent(rows)
    print(f"exponent p={p_fit}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
