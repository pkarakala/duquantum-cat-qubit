"""Truncation convergence: sweep Na and Nb separately and summarize as a record's 'convergence' block.

Two truncations agreeing is necessary, not sufficient (the 20x6 trap of RESEARCH §9): every
alpha needs its own sweep, with top-Fock populations monitored alongside the key quantity.
"""


def sweep(fn, axis, values, fixed) -> list[dict]:
    """[{axis: v, **fixed, **fn(**fixed, axis=v)} for v in values]; fn returns a dict of floats."""
    return [{axis: v, **fixed, **fn(**fixed, **{axis: v})} for v in values]


def converged_at(rows, key, var, tol):
    """Smallest value of `var` whose result is within tol of the largest-N result."""
    ref = rows[-1][key]
    for r in rows:
        if all(abs(s[key] - ref) <= tol * abs(ref) for s in rows if s[var] >= r[var]):
            return r[var]
    return rows[-1][var]


def convergence_block(sweeps: dict, key: str, rel_tol: float, chosen: dict) -> dict:
    """sweeps = {'Na': (fixed_dict, rows), 'Nb': (fixed_dict, rows)}; returns the CONTRACT §6.2 block.

    converged is True iff, for every axis, there are >= 2 rows, chosen[axis] >= needed[axis],
    and the two largest truncations agree within rel_tol.
    """
    if not sweeps:
        raise ValueError("convergence_block needs at least one swept axis")
    out, needed, converged = {}, {}, True
    for axis, (fixed, rows) in sweeps.items():
        if axis not in chosen:
            raise ValueError(f"chosen truncation has no value for swept axis {axis!r}")
        if not rows:
            raise ValueError(f"sweep over {axis!r} has no rows")
        rows = sorted(rows, key=lambda r: r[axis])
        results = [float(r[key]) for r in rows]
        out[axis] = {"fixed": dict(fixed), "values": [r[axis] for r in rows], "results": results}
        needed[axis] = converged_at(rows, key, axis, rel_tol)
        converged = (converged and len(rows) >= 2 and chosen[axis] >= needed[axis]
                     and abs(results[-1] - results[-2]) <= rel_tol * abs(results[-1]))
    return {"key": key, "rel_tol": rel_tol, "sweeps": out, "needed": needed, "converged": bool(converged)}
