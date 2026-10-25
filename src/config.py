"""Every parameter in one place, with the 2*pi applied exactly once.

Units (challenge Section 0.5): time in microseconds, rates and couplings in rad/us.
Values are the fitted experimental parameters from Reglade et al. (Table S2).
"""
import math

import dynamiqs as dq

dq.set_precision("double")     # 32-bit floats are too coarse for slow decays
dq.set_progress_meter(False)

TWO_PI = 2 * math.pi

G2 = TWO_PI * 0.763            # two-photon exchange memory <-> buffer
KAPPA_B = TWO_PI * 2.6         # buffer single-photon loss
KAPPA_A = TWO_PI * 9.3e-3      # memory single-photon loss (phase flips)
ALPHA = 2.1                    # target cat amplitude
EPS_D = ALPHA**2 * G2          # buffer drive, so alpha^2 = eps_d / g2

KAPPA_2 = 4 * G2**2 / KAPPA_B  # effective two-photon dissipation (adiabatic elimination)

N_SINGLE = 30                  # truncation for the one-mode warm-up (Task 1.0)
NA_START, NB_START = 24, 6     # starter truncations from the prompt (not converged, see Task 1.2)
NA, NB = 32, 12                # converged truncations chosen in Task 1.2

# The default solver tolerance leaves ~1e-4 noise in small populations (the truncation
# monitors) and biases the steady buffer population, so tighten it everywhere.
METHOD = dq.method.Tsit5(rtol=1e-8, atol=1e-10)

if __name__ == "__main__":
    print(f"kappa_2/2pi = {KAPPA_2 / TWO_PI:.3f} MHz (expect 0.896)")
    print(f"g2/kappa_b = {G2 / KAPPA_B:.2f}, eps_d/kappa_b = {EPS_D / KAPPA_B:.2f}")
    print(f"phase-flip time 1/(2 kappa_a alpha^2) = {1 / (2 * KAPPA_A * ALPHA**2):.2f} us")
