"""Gamma_X (and Gamma_Z) from the Liouvillian spectrum, one job per (alpha, truncation, knobs).

    python -m research.s2.gx_eig --alpha 2.1 --na 28 --nb 8
    python -m research.s2.gx_eig --model one --alpha 1.4 --na 40 --ka-scale 2
    python -m research.s2.gx_eig --alpha 1.4 --na 22 --nb 8 --eps-z 0.5      # eps_z in units of g2

With eps_z = 0 the a -> -a symmetry splits L into parity blocks and Gamma_X is the slowest
eigenvalue of the odd block. eps_z != 0 breaks it, so we take the slowest nonzero eigenvalue
of the full L (shift-invert just right of the steady state's zero eigenvalue).
"""
import argparse
import time

import numpy as np

from src import spectral as S
from research.s2.common import G2, KAPPA_A, KAPPA_B, KAPPA_2, save


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--alpha", type=float, required=True)
    p.add_argument("--na", type=int, required=True)
    p.add_argument("--nb", type=int, default=8)
    p.add_argument("--model", choices=["one", "two"], default="two")
    p.add_argument("--ka-scale", type=float, default=1.0, help="multiply kappa_a (channel test)")
    p.add_argument("--nth", type=float, default=0.0)
    p.add_argument("--eps-z", type=float, default=0.0, help="readout drive, units of g2")
    p.add_argument("--kb-scale", type=float, default=1.0, help="multiply kappa_b (hardware knob)")
    p.add_argument("--no-gz", action="store_true")
    a = p.parse_args()

    ka = KAPPA_A * a.ka_scale
    kb = KAPPA_B * a.kb_scale
    k2 = 4 * G2**2 / kb
    ez = a.eps_z * G2
    t0 = time.time()
    if a.model == "one":
        H, J, _ = S.one_mode(a.na, k2, a.alpha, ka, n_th=a.nth, eps_z=ez)
        dims = (a.na,)
    else:
        H, aa, bb = S.hamiltonian_two_mode(a.na, a.nb, G2, a.alpha**2 * G2, eps_z=ez)
        J = S.jumps_two_mode(aa, bb, kb, ka, n_th=a.nth)
        dims = (a.na, a.nb)
    L = S.liouvillian(H, J)
    out = {"alpha": a.alpha, "model": a.model, "na": a.na, "nb": a.nb if a.model == "two" else None,
           "kappa_a": ka, "kappa_b": kb, "kappa_2": k2, "n_th": a.nth, "eps_z_over_g2": a.eps_z,
           "dim_L": L.shape[0]}
    if a.eps_z == 0:
        gx, vals = S.gamma_x_odd(L, dims)
        out["gamma_x"] = gx
        out["odd_eigs"] = [[v.real, v.imag] for v in vals]
        if not a.no_gz:
            gz, ve = S.gamma_z_even(L, dims)
            out["gamma_z_eig"] = gz
            out["even_eigs"] = [[v.real, v.imag] for v in ve]
    else:
        vals = S.slowest(L, k=4, sigma=-1e-3)
        out["full_eigs"] = [[v.real, v.imag] for v in vals]
        out["gamma_x"] = -sorted(vals.real, key=abs)[1]
    out["ch1"] = S.gamma_x_channel1(a.alpha, ka)
    out["ch2"] = S.gamma_x_channel2(a.alpha, ka, k2)
    out["gz_theory"] = S.gamma_z_theory(a.alpha, ka)
    out["seconds"] = time.time() - t0
    tag = (f"gx_{a.model}_a{a.alpha:.2f}_{a.na}x{a.nb if a.model == 'two' else 0}"
           f"_ka{a.ka_scale:g}_nth{a.nth:g}_ez{a.eps_z:g}_kb{a.kb_scale:g}")
    print(f"{tag}: Gamma_X = {out['gamma_x']:.5e} /us  ({out['seconds']:.1f} s)")
    save(tag, out)


if __name__ == "__main__":
    main()
