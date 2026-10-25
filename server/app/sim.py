"""Live dynamiqs simulations. Hamiltonians come from src.model or an ExprTree.

l0-core is not on this branch, so src.model.one_mode / two_mode have no drive
arguments. `_two_mode_compat` adds eps_z (a+a†) and eps_x i(a†-a) locally
until that merge. Remove it after l0-core lands.
"""
import inspect
import logging
import os
import time

import jax
import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

from src import config as C
from src import model
from src.analysis import memory_state, top_projector

from server.app.cache import params_hash
from server.app.expr import ExprError, compile_tree, to_python, validate
from server.app.limits import TWO_MODE_N_T
from server.app.settings import ENGINE

log = logging.getLogger("academy.sim")

WIGNER_PIXELS = 81
TWO_METHOD = dq.method.Tsit5(rtol=1e-6, atol=1e-8)
_COMPAT_LOGGED = False


def enable_jax_cache() -> str | None:
    """Persistent JAX cache. Skip it when the directory is not writable."""
    path = os.environ.get("JAX_COMPILATION_CACHE_DIR", "/cache/jax")
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_probe")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("ok")
        os.remove(probe)
    except OSError:
        log.warning("JAX compilation cache unavailable at %s; startup warm-up only", path)
        return None
    jax.config.update("jax_compilation_cache_dir", path)
    log.info("JAX compilation cache %s", path)
    return path


enable_jax_cache()


def _log_compat() -> None:
    global _COMPAT_LOGGED
    if _COMPAT_LOGGED:
        return
    _COMPAT_LOGGED = True
    log.warning(
        "DECISION NEEDED: src.model has no eps_x/coherent2; "
        "server.app.sim._two_mode_compat supplies drives until l0-core merges"
    )


def _supports(fn, name: str) -> bool:
    return name in inspect.signature(fn).parameters


def _drop_zero(jumps: list) -> list:
    kept = []
    for jump in jumps:
        arr = jump.to_jax() if hasattr(jump, "to_jax") else jnp.asarray(jump)
        if float(jnp.linalg.norm(arr)) > 1e-15:
            kept.append(jump)
    return kept


def _drive_terms(a, eps_z: float, eps_x: float) -> list:
    terms = []
    if float(eps_z) != 0.0:
        terms.append(float(eps_z) * (a + a.dag()))
    if float(eps_x) != 0.0:
        terms.append(float(eps_x) * (1j * (a.dag() - a)))
    return terms


def _loss_jumps(a, kappa_a: float, n_th: float) -> list:
    if float(kappa_a) == 0.0:
        return []
    if float(n_th) < 0.0:
        raise ExprError("n_th must be >= 0")
    jumps = [jnp.sqrt(kappa_a * (1.0 + n_th)) * a]
    if float(n_th) > 0.0:
        jumps.append(jnp.sqrt(kappa_a * n_th) * a.dag())
    return jumps


def _two_mode_compat(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th, eps_z, eps_x):
    """Call src.model.two_mode, then add drives the unmerged signature lacks."""
    compat = not _supports(model.two_mode, "eps_z")
    if compat:
        _log_compat()
    kwargs = {}
    if _supports(model.two_mode, "n_th"):
        kwargs["n_th"] = n_th
    if _supports(model.two_mode, "eps_z"):
        kwargs["eps_z"] = eps_z
    if _supports(model.two_mode, "eps_x"):
        kwargs["eps_x"] = eps_x
    model_ka = 0.0 if compat and float(n_th) != 0.0 else kappa_a
    H, jumps, ops = model.two_mode(Na, Nb, g2, eps_d, kappa_b, model_ka, **kwargs)
    a, b = ops
    if compat:
        for term in _drive_terms(a, eps_z, eps_x):
            H = H + term
        if float(n_th) != 0.0:
            jumps = list(jumps) + _loss_jumps(a, kappa_a, n_th)
    return H, _drop_zero(list(jumps)), (a, b)


def _one_mode_ops(N, kappa_2, alpha, kappa_a, n_th, eps_z, eps_x, delta):
    compat = not _supports(model.one_mode, "eps_z")
    if compat and (float(eps_z) != 0.0 or float(eps_x) != 0.0 or float(n_th) != 0.0):
        _log_compat()
    kwargs = {}
    if _supports(model.one_mode, "n_th"):
        kwargs["n_th"] = n_th
    if _supports(model.one_mode, "eps_z"):
        kwargs["eps_z"] = eps_z
    if _supports(model.one_mode, "eps_x"):
        kwargs["eps_x"] = eps_x
    model_ka = 0.0 if compat and float(n_th) != 0.0 else kappa_a
    H, jumps, a = model.one_mode(N, kappa_2, alpha, model_ka, **kwargs)
    if compat:
        for term in _drive_terms(a, eps_z, eps_x):
            H = H + term
        if float(n_th) != 0.0:
            jumps = list(jumps) + _loss_jumps(a, kappa_a, n_th)
    if float(delta) != 0.0:
        H = H + float(delta) * (a.dag() @ a)
    return H, _drop_zero(list(jumps)), a


def _dm_array(rho):
    arr = rho.to_jax() if hasattr(rho, "to_jax") else jnp.asarray(rho)
    arr = jnp.asarray(arr)
    if arr.ndim == 2 and arr.shape[0] == arr.shape[1]:
        return arr
    ket = arr.reshape((-1,))
    return jnp.outer(ket, jnp.conj(ket))


def _expect(op, dm):
    opj = op.to_jax() if hasattr(op, "to_jax") else jnp.asarray(op)
    return jnp.trace(opj @ dm)


def _todm(ket):
    if hasattr(dq, "todm"):
        return dq.todm(ket)
    return ket @ ket.dag()


def _ket_one(N: int, kind: str, alpha: float, n: int):
    if kind == "vacuum":
        return dq.fock(N, 0)
    if kind == "coherent":
        return dq.coherent(N, alpha)
    if kind == "cat_plus":
        return dq.unit(dq.coherent(N, alpha) + dq.coherent(N, -alpha))
    if kind == "cat_minus":
        return dq.unit(dq.coherent(N, alpha) - dq.coherent(N, -alpha))
    if kind == "fock":
        if n < 0 or n >= N:
            raise ExprError(f"fock n={n} is outside 0..{N - 1}")
        return dq.fock(N, n)
    raise ExprError(f"unknown init {kind}")


def _init_one(N: int, kind: str, alpha: float, n: int):
    return _todm(_ket_one(N, kind, alpha, n))


def _init_two(Na: int, Nb: int, kind: str, alpha: float, n: int):
    if kind == "vacuum" and hasattr(model, "vacuum2"):
        ket = model.vacuum2(Na, Nb)
    elif kind == "coherent" and hasattr(model, "coherent2"):
        ket = model.coherent2(Na, Nb, alpha)
    elif kind in ("cat_plus", "cat_minus") and hasattr(model, "cat2"):
        sign = 1 if kind == "cat_plus" else -1
        ket = model.cat2(Na, Nb, alpha, sign=sign)
    else:
        if kind != "vacuum":
            _log_compat()
        ket = dq.tensor(_ket_one(Na, kind, alpha, n), dq.fock(Nb, 0))
    return _todm(ket)


def _as_series(values) -> list[float]:
    return [float(v) for v in np.real(np.asarray(values)).reshape(-1)]


def _solve(H, jumps, rho0, t_end: float, n_t: int, method, extra):
    t = jnp.linspace(0.0, float(t_end), int(n_t))
    res = dq.mesolve(H, jumps, rho0, t, method=method, save_states=False, save_extra=extra)
    return [float(v) for v in np.asarray(t)], res.extra


def _wigner_pack(states, times) -> dict:
    frames = []
    x = y = None
    for state, t in zip(states, times):
        xvec, yvec, wigner = dq.wigner(state, xmax=4.0, ymax=4.0, npixels=WIGNER_PIXELS)
        if x is None:
            x = [float(v) for v in np.asarray(xvec)]
            y = [float(v) for v in np.asarray(yvec)]
        frames.append({"t_us": float(t), "w": np.real(np.asarray(wigner)).tolist()})
    return {"x": x, "y": y, "frames": frames}


def _wigner_frames(H, jumps, rho0, times, method, reduce=None):
    if not times:
        return None
    order = sorted(range(len(times)), key=lambda i: float(times[i]))
    ordered = [float(times[i]) for i in order]
    res = dq.mesolve(
        H, jumps, rho0, jnp.asarray(ordered), method=method, save_states=True,
    )
    states = []
    for state in res.states:
        states.append(reduce(state) if reduce else state)
    packed = _wigner_pack(states, ordered)
    # Restore the caller's time order.
    by_t = {frame["t_us"]: frame for frame in packed["frames"]}
    packed["frames"] = [by_t[float(t)] for t in times]
    return packed


def _meta(req: dict, wall_ms: int, compiled: str | None = None) -> dict:
    meta = {
        "engine": ENGINE,
        "cached": False,
        "wall_ms": wall_ms,
        "params_hash": params_hash(req),
    }
    if compiled is not None:
        meta["compiled"] = compiled
    return meta


def _finish(req, outputs, body, t0, compiled=None) -> dict:
    wall = int(round((time.perf_counter() - t0) * 1000))
    kept = {"t_us": body["t_us"], "meta": _meta(req, wall, compiled)}
    for name in outputs:
        if name in body:
            kept[name] = body[name]
    if "final_pops" in body and req.get("modes", "one") != "two":
        kept["final_pops"] = body["final_pops"]
    if "top2" in body and "n" in outputs:
        kept["top2"] = body["top2"]
    return kept


def _one_body(H, jumps, a, rho0, req, method) -> dict:
    N = int(a.shape[-1]) if hasattr(a, "shape") else int(req["N"])
    n_op = a.dag() @ a
    parity = dq.parity(N)

    def extra(_t, rho):
        dm = _dm_array(rho)
        return {
            "n": jnp.real(_expect(n_op, dm)),
            "parity": jnp.real(_expect(parity, dm)),
            "re_a": jnp.real(_expect(a, dm)),
            "top2": jnp.real(dm[-1, -1] + dm[-2, -2]),
            "pops": jnp.real(jnp.diag(dm)),
        }

    t_us, got = _solve(H, jumps, rho0, float(req["t_end_us"]), int(req["n_t"]), method, extra)
    pops = np.real(np.asarray(got["pops"]))
    body = {
        "t_us": t_us,
        "n": _as_series(got["n"]),
        "parity": _as_series(got["parity"]),
        "re_a": _as_series(got["re_a"]),
        "top2": _as_series(got["top2"]),
        "final_pops": [float(v) for v in pops[-1]],
    }
    times = list(req.get("wigner_times") or [])
    if "wigner" in req.get("outputs", []) and not times:
        times = [float(req["t_end_us"])]
    if "wigner" in req.get("outputs", []):
        body["wigner"] = _wigner_frames(H, jumps, rho0, times, method)
    return body


def _two_body(H, jumps, a, b, rho0, req, Na, Nb) -> dict:
    na = a.dag() @ a
    nb = b.dag() @ b
    parity = dq.tensor(dq.parity(Na), dq.eye(Nb))
    top2 = dq.tensor(top_projector(Na, 2), dq.eye(Nb))
    topb = dq.tensor(dq.eye(Na), top_projector(Nb, 1))

    def extra(_t, rho):
        dm = _dm_array(rho)
        expect_b = _expect(b, dm)
        return {
            "na": jnp.real(_expect(na, dm)),
            "nb": jnp.real(_expect(nb, dm)),
            "b_re": jnp.real(expect_b),
            "b_im": jnp.imag(expect_b),
            "top2_a": jnp.real(_expect(top2, dm)),
            "top_b": jnp.real(_expect(topb, dm)),
            "parity": jnp.real(_expect(parity, dm)),
        }

    # Live HTTP calls omit n_t and stay at 201. Precompute may pass a finer grid.
    n_t = int(req["n_t"]) if req.get("n_t") else TWO_MODE_N_T
    t_us, got = _solve(H, jumps, rho0, float(req["t_end_us"]), n_t, TWO_METHOD, extra)
    body = {"t_us": t_us}
    for name in ("na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity"):
        body[name] = _as_series(got[name])
    times = list(req.get("wigner_times") or [])
    if "wigner" in req.get("outputs", []) and not times:
        times = [float(req["t_end_us"])]
    if "wigner" in req.get("outputs", []):
        body["wigner"] = _wigner_frames(
            H, jumps, rho0, times, TWO_METHOD, reduce=lambda st: memory_state(st, Na, Nb),
        )
    return body


def _alpha(req: dict, fallback: float) -> float:
    if req.get("init_alpha") is not None:
        return float(req["init_alpha"])
    if req.get("alpha") is not None:
        return float(req["alpha"])
    return float(fallback)


def run_one_mode(req: dict) -> dict:
    """Effective cat model through src.model.one_mode. Drives are eps_*_over_g2 * G2."""
    t0 = time.perf_counter()
    alpha = float(req["alpha"])
    N = int(req["N"])
    kappa_2 = float(req.get("kappa2_scale", 1.0)) * float(C.KAPPA_2)
    kappa_a = float(req.get("kappa_a_scale", 1.0)) * float(C.KAPPA_A)
    eps_z = float(req.get("eps_z_over_g2", 0.0)) * float(C.G2)
    eps_x = float(req.get("eps_x_over_g2", 0.0)) * float(C.G2)
    # delta_over_2pi_MHz is a frequency in MHz. omega = 2π f, and TWO_PI lives in config.
    delta = float(req.get("delta_over_2pi_MHz") or 0.0) * float(C.TWO_PI)
    H, jumps, a = _one_mode_ops(
        N, kappa_2, alpha, kappa_a, float(req.get("n_th") or 0.0), eps_z, eps_x, delta,
    )
    rho0 = _init_one(N, req.get("init", "vacuum"), _alpha(req, alpha), int(req.get("init_n") or 0))
    body = _one_body(H, jumps, a, rho0, req, C.METHOD)
    return _finish(req, req.get("outputs") or [], body, t0)


def run_two_mode(req: dict) -> dict:
    """Memory + buffer through src.model.two_mode. Live traces use n_t = 201."""
    t0 = time.perf_counter()
    Na, Nb = int(req["Na"]), int(req["Nb"])
    alpha = float(req["alpha"])
    g2 = float(C.G2) * float(req.get("g2_scale", 1.0))
    eps_d = alpha ** 2 * g2
    kappa_b = float(C.KAPPA_B) * float(req.get("kappa_b_scale", 1.0))
    kappa_a = float(C.KAPPA_A) * float(req.get("kappa_a_scale", 1.0))
    eps_z = float(req.get("eps_z_over_g2", 0.0)) * float(C.G2)
    eps_x = float(req.get("eps_x_over_g2", 0.0)) * float(C.G2)
    H, jumps, (a, b) = _two_mode_compat(
        Na, Nb, g2, eps_d, kappa_b, kappa_a, float(req.get("n_th") or 0.0), eps_z, eps_x,
    )
    rho0 = _init_two(Na, Nb, req.get("init", "vacuum"), _alpha(req, alpha), int(req.get("init_n") or 0))
    body = _two_body(H, jumps, a, b, rho0, req, Na, Nb)
    return _finish(req, req.get("outputs") or [], body, t0)


def _as_hamiltonian(H, modes: str, N, Na, Nb):
    if isinstance(H, dq.QArray):
        return H
    if isinstance(H, (int, float, complex)):
        if modes == "one":
            return complex(H) * dq.eye(int(N))
        return complex(H) * dq.eye(int(Na), int(Nb))
    raise ExprError("H did not compile to an operator")


def run_expr(req: dict) -> dict:
    """Compile an allowlisted ExprTree. User source code is never executed."""
    t0 = time.perf_counter()
    modes = req["modes"]
    params = req.get("params") or {}
    validate(req["H"], modes=modes, params=params, role="H")
    for jump in req.get("jumps") or []:
        validate(jump, modes=modes, params=params, role="jump")
    if modes == "one":
        N = int(req["N"])
        H = _as_hamiltonian(compile_tree(req["H"], "one", N=N, params=params), "one", N, None, None)
        jumps = []
        for jump in req.get("jumps") or []:
            compiled = compile_tree(jump, "one", N=N, params=params)
            if not isinstance(compiled, dq.QArray):
                raise ExprError("jump must be an operator")
            jumps.append(compiled)
        a = dq.destroy(N)
        rho0 = _init_one(N, req.get("init", "vacuum"), _alpha(req, float(C.ALPHA)), int(req.get("init_n") or 0))
        body = _one_body(H, _drop_zero(jumps), a, rho0, req, C.METHOD)
        return _finish(req, req.get("outputs") or [], body, t0, compiled=to_python(req["H"]))
    Na, Nb = int(req["Na"]), int(req["Nb"])
    H = _as_hamiltonian(
        compile_tree(req["H"], "two", Na=Na, Nb=Nb, params=params), "two", None, Na, Nb,
    )
    jumps = []
    for jump in req.get("jumps") or []:
        compiled = compile_tree(jump, "two", Na=Na, Nb=Nb, params=params)
        if not isinstance(compiled, dq.QArray):
            raise ExprError("jump must be an operator")
        jumps.append(compiled)
    a, b = dq.destroy(Na, Nb)
    rho0 = _init_two(Na, Nb, req.get("init", "vacuum"), _alpha(req, float(C.ALPHA)), int(req.get("init_n") or 0))
    shaped = dict(req)
    shaped["t_end_us"] = float(req["t_end_us"])
    body = _two_body(H, _drop_zero(jumps), a, b, rho0, shaped, Na, Nb)
    return _finish(req, req.get("outputs") or [], body, t0, compiled=to_python(req["H"]))


def pool_worker(kind: str, payload: dict) -> dict:
    """Process-pool entry point. The child imports this module, not main."""
    if kind == "one":
        return run_one_mode(payload)
    if kind == "two":
        return run_two_mode(payload)
    if kind == "expr":
        return run_expr(payload)
    raise ValueError(f"unknown sim kind {kind}")


def warmup() -> dict:
    """Compile the live Hilbert spaces. Two-mode uses the fixed n_t of 201."""
    one = {
        "alpha": float(C.ALPHA),
        "kappa2_scale": 1.0,
        "kappa_a_scale": 1.0,
        "N": 30,
        "t_end_us": 0.05,
        "n_t": 5,
        "init": "vacuum",
        "outputs": ["n"],
    }
    two = {
        "alpha": float(C.ALPHA),
        "Na": 16,
        "Nb": 5,
        "t_end_us": 0.05,
        "init": "vacuum",
        "outputs": ["na"],
    }
    out = {}
    t0 = time.perf_counter()
    run_one_mode(one)
    out["one_mode_warmup_s"] = round(time.perf_counter() - t0, 3)
    t0 = time.perf_counter()
    run_two_mode(two)
    out["two_mode_warmup_s"] = round(time.perf_counter() - t0, 3)
    log.info("warmup %s", out)
    return out
