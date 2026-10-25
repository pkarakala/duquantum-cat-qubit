"""Task 2.4a: which terms of the pumped ATS survive the rotating-wave approximation.

H_ATS = 2 E_J eps_p cos(w_p t) sin(phi),  phi = phi_a (a + a^dag) + phi_b (b + b^dag).
Normal-ordered exactly (BCH): sin(phi) = e^{-Phi/2} sum over odd p+q+r+s of
    i^{p+q+r+s-1} phi_a^{p+q} phi_b^{r+s} / (p! q! r! s!)  a^dag^p a^q b^dag^r b^s     (Phi = phi_a^2 + phi_b^2)
In the frame rotating at w_a, w_b a monomial picks up e^{i[(p-q) w_a + (r-s) w_b] t}; times the pump
e^{+-i w_p t} it is static (resonant) when (p-q) w_a + (r-s) w_b = -+ w_p. With an extra memory
drive at w_d (readout, 2.4a) a term can also be resonant with the drive alone.
Prints every term up to --order with its detuning and coefficient (MHz, includes the 1/2 from the cosine).

    python -m research.s2.rwa_terms --order 7
"""
import argparse
import itertools
import math

WA, WB, WP = 4.0e3, 4.8e3, 3.2e3         # MHz (ordinary frequency)
EJ, PA, PB = 40e3, 0.06, 0.3             # MHz, zero-point phases


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--order", type=int, default=7)
    p.add_argument("--window", type=float, default=200.0, help="report terms within this detuning (MHz)")
    a = p.parse_args()
    Phi = PA**2 + PB**2
    g2_lead = 0.5 * EJ * PA**2 * PB * math.exp(-Phi / 2)          # per unit eps_p
    eps_p = 0.763 / g2_lead
    print(f"e^(-Phi/2) = {math.exp(-Phi/2):.4f};  g2 = 1/2 E_J eps_p phi_a^2 phi_b e^(-Phi/2)  ->  eps_p = {eps_p:.4f} for g2/2pi = 0.763 MHz")
    rows = []
    for n in range(1, a.order + 1, 2):
        for p_, q, r, s in itertools.product(range(n + 1), repeat=4):
            if p_ + q + r + s != n:
                continue
            w = (p_ - q) * WA + (r - s) * WB
            coef = 2 * EJ * eps_p * 0.5 * math.exp(-Phi / 2) * PA**(p_ + q) * PB**(r + s) / (
                math.factorial(p_) * math.factorial(q) * math.factorial(r) * math.factorial(s))
            for sgn, lab in ((+1, "pump e^{-i wp t}"), (-1, "pump e^{+i wp t}")):
                det = w - sgn * WP
                if abs(det) <= a.window and (p_, q, r, s) <= (q, p_, s, r):   # keep one of each h.c. pair
                    rows.append((abs(det), n, p_, q, r, s, coef, lab))
    rows.sort()
    print(f"{'det(MHz)':>9} {'order':>5}  term                       coef(MHz)")
    for det, n, p_, q, r, s, c, lab in rows:
        term = f"a†^{p_} a^{q} b†^{r} b^{s}"
        print(f"{det:9.1f} {n:5d}  {term:26s} {c:10.4g}   ({lab}, + h.c.)")


if __name__ == "__main__":
    main()
