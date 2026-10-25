"""Resonant ATS exchange beyond the cubic approximation, Task 2.4.

The pump phase is chosen to make the cubic exchange positive, matching src.model.
The sine model keeps all phase orders at the fundamental pump harmonic; it is
still a rotating-wave model, not a simulation of the GHz circuit or its bath.
"""
import numpy as np
from math import factorial
from scipy.sparse import coo_matrix
from scipy.special import eval_genlaguerre, j1

from src.rate_solver import operators

PHI_A, PHI_B = 0.06, 0.30
EJ = 2*np.pi*40000.0  # angular frequency in inverse microseconds
OMEGA_A, OMEGA_B = 2*np.pi*4000, 2*np.pi*4800


def pump_amplitude(g2):
    return 2*g2/(EJ*PHI_A**2*PHI_B)


def exchange_factor(n, m, g2, order="cubic"):
    """Correction for |n,m> -> |n-2,m+1>, relative to cubic g2 a² b†."""
    n, m = np.asarray(n), np.asarray(m)
    x, y = PHI_A**2, PHI_B**2
    v = x+y
    if order == "cubic":
        return np.ones(np.broadcast_shapes(n.shape, m.shape))
    first = (n-2)*x/3 + m*y/2
    if order == "fifth":
        return 1-v/2-first
    if order == "seventh":
        second = ((n-2)*(n-3)*x*x/24 + m*(m-1)*y*y/12
                  + (n-2)*m*x*y/6)
        return 1-v/2+v*v/8-first*(1-v/2)+second
    if order == "sine":
        phase = (np.exp(-v/2)*2*eval_genlaguerre(n-2, 2, x)/(n*(n-1))
                 * eval_genlaguerre(m, 1, y)/(m+1))
        epsilon_p = pump_amplitude(g2)
        return phase*(2*j1(epsilon_p)/epsilon_p)
    raise ValueError("Expected cubic, fifth, seventh or sine exchange")


def exchange(Na, Nb, g2, order="cubic"):
    """Sparse lowering-memory/raising-buffer part of the physical Hamiltonian."""
    n, m = np.meshgrid(np.arange(2, Na), np.arange(Nb-1), indexing="ij")
    values = g2*np.sqrt(n*(n-1)*(m+1))*exchange_factor(n, m, g2, order)
    return coo_matrix((values.ravel(), (((n-2)*Nb+m+1).ravel(),
                                       (n*Nb+m).ravel())),
                      shape=(Na*Nb, Na*Nb)).tocsc()


def buffer_drive(alpha, g2, order="cubic"):
    """Calibrate <dot b>=0 at |alpha,0> before including memory loss.

    Higher orders use the infinite-Fock coherent expectation. The short sine
    series is 2 J2(2 phi_a alpha)/(phi_a alpha)²; its next term is below 1e-30
    over the delivered amplitude range. Algebra also accepts a JAX tracer.
"""
    if order == "cubic":
        return g2*alpha**2
    v, u = PHI_A**2+PHI_B**2, (PHI_A*alpha)**2
    if order == "fifth":
        factor = 1-v/2-u/3
    elif order == "seventh":
        factor = 1-v/2+v*v/8-u*(1-v/2)/3+u*u/24
    elif order == "sine":
        epsilon_p = pump_amplitude(g2)
        factor = (np.exp(-v/2)*2*j1(epsilon_p)/epsilon_p
                  * sum(2*(-u)**k/(factorial(k)*factorial(k+2)) for k in range(9)))
    else:
        raise ValueError("Unknown circuit order")
    return g2*alpha**2*factor


def rotating_model(Na, Nb, alpha, g2, epsilon_z, order="cubic"):
    a, b = operators(Na, Nb)
    T = exchange(Na, Nb, g2, order)
    eps_d = buffer_drive(alpha, g2, order)
    return T+T.T-eps_d*(b+b.T)+epsilon_z*(a+a.T), (a, b)
