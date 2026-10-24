"""Write the tiny Lab-exporter fixtures (4 records + a 3-frame 5x5 Wigner npz)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent / "results"
RECORDS = ROOT / "records"
ARRAYS = ROOT / "arrays"

PARAMS = {
    "g2_MHz": 0.763,
    "kappa_b_MHz": 2.6,
    "kappa_a_kHz": 9.3,
    "alpha": 1.0,
    "n_th": 0.0,
    "eps_z_over_g2": 0.0,
}


def rec(rid: str, task: str, quantity: str, value: float, method: str, extra: dict | None = None) -> dict:
    body = {
        "schema": "duq.record/v2",
        "id": rid,
        "task": task,
        "quantity": quantity,
        "value": value,
        "uncertainty": value * 1e-4,
        "units": "1/us" if "gamma" in quantity else "photons",
        "method": method,
        "params": {**PARAMS, **({"alpha": 2.1} if rid.startswith("t1_1") else {})},
        "truncation": {"Na": 20, "Nb": 6},
        "convergence": {
            "key": quantity,
            "rel_tol": 0.001,
            "sweeps": {
                "Na": {"fixed": {"Nb": 6}, "values": [16, 20], "results": [value * 1.01, value]},
            },
            "needed": {"Na": 16},
            "converged": True,
        },
        "cross_check": [
            {"method": "analytic_coth" if quantity == "gamma_z" else "larger_truncation", "ref_id": None, "value": value * 0.999, "rel_diff": 0.001, "tol": 0.02, "agree": True}
        ],
        "artifacts": None,
        "notes": "fixture",
        "provenance": {"script": "site/test/fixtures/make_fixtures.py", "git_commit": "deadbee", "dirty": False},
    }
    if extra:
        body.update(extra)
    return body


def main() -> None:
    RECORDS.mkdir(parents=True, exist_ok=True)
    ARRAYS.mkdir(parents=True, exist_ok=True)
    records = [
        rec("t1_1.peak_na.td.two_mode.a2.10", "1.1", "peak_na", 6.89, "mesolve_peak"),
        rec("t2_1.gamma_x.eig.one_mode.a1.00.nth0", "2.1", "gamma_x", 2.26e-3, "liouvillian_eig_odd_sector"),
        rec("t2_1.gamma_x.eig.two_mode.a1.00.nth0", "2.1", "gamma_x", 2.28e-3, "liouvillian_eig_odd_sector"),
        rec("t2_2.gamma_z.td.two_mode.a1.00", "2.2", "gamma_z", 0.1212, "time_domain_fit_exp_offset"),
    ]
    for r in records:
        (RECORDS / f"{r['id']}.json").write_text(json.dumps(r, indent=2) + "\n")

    x = np.linspace(-1.0, 1.0, 5)
    y = np.linspace(-1.0, 1.0, 5)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    frames = np.stack([np.exp(-((xx - 0.2 * k) ** 2 + yy**2)) for k in range(3)])
    t_us = np.linspace(0.0, 1.0, 11)
    na = 4.41 * (1.0 - np.exp(-t_us))
    nb = 0.3 * np.sin(np.pi * t_us) ** 2
    np.savez(
        ARRAYS / "lab.inflation_wigner.npz",
        t_us=t_us,
        na=na,
        nb=nb,
        top2_a=1e-8 * np.ones_like(t_us),
        top_b=1e-8 * np.ones_like(t_us),
        eff_t_us=t_us,
        eff_na=4.41 * (1.0 - np.exp(-2.0 * t_us)),
        x=x,
        y=y,
        frames=frames,
        frame_t_us=np.array([0.0, 0.5, 1.0]),
    )
    print(f"wrote {RECORDS} ({len(records)} records) and {ARRAYS / 'lab.inflation_wigner.npz'}")


if __name__ == "__main__":
    main()
