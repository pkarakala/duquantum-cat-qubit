# Task 2.3: transmon-free memory-bit readout

The aim is to distinguish the two memory codewords through the emitted buffer
field. A weak memory drive transfers the codeword sign into opposite real
buffer amplitudes, providing a readout signal without a transmon.

At $\epsilon_Z=0.05g_2$, the real-field separation is **0.02378968**,
**0.0834% below** the leading linear estimate. The response undergoes damped
oscillation and satisfies a sustained 1% settling criterion from **0.968 µs**.
The calculation resolves conditional ensemble means over a finite interval.

## Protocol and observables

Let $a$ and $b$ annihilate a photon in the memory and buffer, respectively.
With $\hbar=1$, we add a constant, real memory drive to the supplied two-photon
Hamiltonian:

$$
H=H_{2\mathrm{ph}}+H_Z,\qquad H_Z=\epsilon_Z(a+a^\dagger),
$$

$$
H_{2\mathrm{ph}}=g_2(a^2b^\dagger+a^{\dagger2}b)-\epsilon_d(b+b^\dagger),
\qquad \epsilon_d=g_2\alpha^2.
$$

Here $g_2$ is the two-photon exchange coupling, $\epsilon_d$ is the buffer-drive
amplitude, and $\alpha=2.1$ is the real target memory amplitude. The jump
operators are $\sqrt{\kappa_a}a$ and $\sqrt{\kappa_b}b$, with $\kappa_a$ and
$\kappa_b$ the memory and buffer photon-loss rates. All
[supplied parameters](../TECHNICAL.md#1-model-and-conventions) are retained.

We choose $\epsilon_Z=0.05g_2=0.23970352\ \mathrm{\mu s}^{-1}$ to probe the
approximately linear response while keeping the displacement about the occupied
well small. Its frequency scale, $\epsilon_Z/(2\pi)=38.15$ kHz, is twenty times
below $g_2/(2\pi)=763$ kHz. The drive sweep below checks linearity; optimizing
the readout strength and its effect on bit-flip protection belongs to Task 2.4.

For $s=\pm1$, let $\rho_s(t)$ be the **joint memory–buffer density matrix**
evolved from $|s\alpha\rangle_a|0\rangle_b$. Both codewords are evolved
independently. Preparation errors are excluded. Production runs use
$(N_a,N_b)=(32,12)$ retained Fock levels and double-precision Tsit5 integration
with relative and absolute tolerances $10^{-10}$ and $10^{-12}$.

Define the memory amplitude and buffer field as

$$
A_s(t)=\mathrm{Tr}(a\rho_s(t)),\qquad
\beta_s(t)=\mathrm{Tr}(b\rho_s(t)).
$$

The drive contributes $\dot A_s=-i\epsilon_Z$, displacing the memory along the
imaginary axis. At the semiclassical level, write $A_s=s\alpha+\delta a_s$,
where $\delta a_s$ is the displacement from the occupied well. Then
$A_s^2-\alpha^2\simeq2s\alpha\delta a_s$: the same displacement produces
opposite real buffer responses. A phase-referenced measurement of the real
buffer-output quadrature can therefore distinguish the memory bit.

We simulate 0–4 µs with 2-ns saved spacing. Let $\bar\beta_s$ be each branch's
complex mean over 3–4 µs. The instantaneous separation, plateau contrast and
common field are

$$
\Delta\beta_R(t)=\mathrm{Re}(\beta_-(t)-\beta_+(t)),\qquad
\Delta\beta_R=\mathrm{Re}(\bar\beta_--\bar\beta_+),\qquad
\beta_{\mathrm{com}}(t)=\frac{\beta_+(t)+\beta_-(t)}{2}.
$$

Settling is measured using the normalized full-complex residual

$$
r(t)=\frac{\max_{s=\pm1}|\beta_s(t)-\bar\beta_s|}
{\epsilon_Z/(2\alpha g_2)}.
$$

The settling time $t_{\mathrm{set}}$ is the first saved time after which
**$r(t)\leq0.01$ at every remaining sample through 4 µs**. This uses both
quadratures and excludes early crossings followed by further ringing.
The 1% tolerance is relative to the predicted half contrast, rather than to
the instantaneous field. Adaptive integration steps are distinct from saved
times. An 8-µs run checks the result against a later 7–8 µs mean. Zero drive has
no signal-relative settling time, represented by JSON null.

## Numerical results

At the nominal drive, the plateau fields are

$$
\bar\beta_+=-0.01189484+0.00311514i,\qquad
\bar\beta_-=+0.01189484+0.00311514i.
$$

Their real parts are opposite; their common imaginary component is a
memory-loss response. With no memory drive, both branches give
$\bar\beta=0.00304907i$ and zero real contrast.

Neglecting memory loss, the leading local estimate is

$$
\beta_s\simeq-\frac{s\epsilon_Z}{2\alpha g_2},\qquad
\Delta_{\mathrm{lin}}=\frac{\epsilon_Z}{\alpha g_2}=0.02380952.
$$

The simulated real contrast, **$\Delta\beta_R=0.02378968$**, is **0.0834% below**
this estimate. The weak-drive sweep confirms proportional response:

| $\epsilon_Z/g_2$ | Real separation | Leading estimate | Relative difference | 1% settling (µs) |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | — | — |
| 0.025 | 0.01189512 | 0.01190476 | −0.0810% | 0.976 |
| **0.050** | **0.02378968** | **0.02380952** | **−0.0834%** | **0.968** |
| 0.100 | 0.04757483 | 0.04761905 | −0.0929% | 0.966 |

Contrast per unit drive varies by only 0.0119% over the nonzero sweep.
At 4 µs, fidelity with the initial coherent codeword is 0.99986 and the signed
real memory amplitude divided by $\alpha$ is 0.99916 for either branch.
These checks support a weak local response over the simulated interval;
they do not establish a long-time switching rate.

The approach is **oscillatory**. The first contrast maximum occurs at
0.158 µs, with **44.3% overshoot** and an approximately **0.313-µs**
peak-spacing period. Both complex fields satisfy the sustained 1% criterion
from **0.968 µs** through 4 µs. The final crossing lies in
**[0.966, 0.968] µs**. Tighter integration with a 1-ns output grid and the
extended run's 7–8 µs plateau both give the same settling time.

<p align="center">
  <img src="../figures/task_2_3_readout.png" width="860" alt="Conditional buffer fields and settling">
</p>

**Buffer response at $\epsilon_Z/g_2=0.05$.** (a) Real fields from the two
initial codewords; dotted lines mark the leading estimates. (b) Common
imaginary field, its zero-drive control, and the leading memory-loss estimate.
(c) Transient real separation divided by $\Delta_{\mathrm{lin}}$, compared
with the local semiclassical response. (d) Residual $r(t)$; dotted and dashed
lines mark the 1% criterion and $t_{\mathrm{set}}=0.968$ µs, respectively.

## Local response and common field

The buffer-fluorescence readout mechanism and leading local estimate follow
[Réglade et al., Supplement S8.5](https://arxiv.org/html/2307.06617v2).
The derivation below explains the common imaginary field and damped transient.

For this real-parameter model, the antiunitary transformation
$\rho\mapsto\Pi_a\Pi_b\rho^*\Pi_b\Pi_a$, where $\Pi_a$ and $\Pi_b$ are the
mode-parity operators and the star denotes complex conjugation in the Fock
basis, maps the two initial conditions into each other while leaving the
evolution invariant. It therefore gives the exact relation

$$
\beta_-(t)=-\beta_+^*(t).
$$

This accounts for opposite real fields and equal imaginary fields. The
independent codeword evolutions test this symmetry numerically.

The exact first-moment equations are

$$
\dot A_s=-2ig_2\langle a^\dagger b\rangle_s-i\epsilon_Z
-\frac{\kappa_a}{2}A_s,\qquad
\dot\beta_s=-ig_2(\langle a^2\rangle_s-\alpha^2)-\frac{\kappa_b}{2}\beta_s.
$$

Factorizing the moments and linearizing about $A_s=s\alpha$, $\beta_s=0$,
define the **complex amplitude deviations**

$$
\delta a_s=A_s-s\alpha,\qquad \delta b_s=\beta_s,\qquad G_s=2sg_2\alpha.
$$

Here $G_s$ is the local exchange coupling. The deviations are semiclassical
amplitudes; the full simulation evolves the density matrix without moment
factorization. To first order,

$$
\delta\dot a_s=-\frac{\kappa_a}{2}\delta a_s-iG_s\delta b_s-i\epsilon_Z
-\frac{\kappa_a s\alpha}{2},\qquad
\delta\dot b_s=-iG_s\delta a_s-\frac{\kappa_b}{2}\delta b_s.
$$

Setting these derivatives to zero gives the local stationary buffer field

$$
\beta_{s,\mathrm{loc}}=
\frac{-\epsilon_ZG_s+i\kappa_as\alpha G_s/2}
{G_s^2+\kappa_a\kappa_b/4}.
$$

To leading order in memory loss, its imaginary part is
$\kappa_a/(4g_2)=0.00304718$, independent of the well sign. The zero-drive
control confirms this background separately from the real readout contrast.

The local linear system has eigenvalues

$$
\lambda_\pm=-\frac{\kappa_a+\kappa_b}{4}
\pm i\sqrt{(2g_2\alpha)^2-\left(\frac{\kappa_b-\kappa_a}{4}\right)^2}.
$$

They predict an underdamped response with a **0.319-µs** oscillation period
and a **0.244-µs** amplitude-envelope time. The local step response is tested
against a matrix-exponential solution. Its approximate period agrees closely
with the full quantum result, while the full quantum trajectory determines the
reported settling time.

## Validation and reproduction

The task script runs these checks before reporting success:

- Positive and negative real buffer fields, exact conjugation symmetry, and
  zero real contrast in the zero-drive control.
- Weak-drive response at $\epsilon_Z/g_2=0.025,0.05,0.10$.
- Separate memory and buffer increases to $(40,12)$ and $(32,14)$, followed by
  their joint increase to $(40,14)$. A smaller $(24,8)$ case is also checked.
- Tighter integration at relative/absolute tolerances $10^{-11}/10^{-13}$,
  with 1-ns saved spacing; an 8-µs horizon at the production tolerances.
- Independent QuTiP BDF integration with separately constructed operators at
  the production cutoff $(32,12)$, isolating integration error from cutoff error.
- Trace throughout the trajectory, final-state Hermiticity and minimum
  eigenvalue. Small signed numerical residuals are retained.

Field differences are normalized by the predicted half contrast,
$\epsilon_Z/(2\alpha g_2)$. The required maximum differences are 0.1% for cutoff
and horizon comparisons and 0.001% for solver comparisons. These are numerical
criteria, not detector performance specifications. The exact thresholds and
all pass/fail results are stored with the data.

| Comparison against $(32,12)$ production | Difference / predicted half contrast |
|---|---:|
| Smaller cutoff $(24,8)$ | $1.02\times10^{-5}$ |
| Memory increase $(40,12)$ | $6.53\times10^{-8}$ |
| Buffer increase $(32,14)$ | $3.54\times10^{-7}$ |
| Joint increase $(40,14)$ | $3.07\times10^{-7}$ |
| Tighter Tsit5 tolerances, 1-ns saves | $1.27\times10^{-8}$ |
| Independent QuTiP BDF, same $(32,12)$ | $1.31\times10^{-7}$ |
| Change from 3–4 to 7–8 µs plateau | $2.44\times10^{-5}$ |

Trajectory comparisons use the maximum complex-field difference over both
codewords and the full 0–4 µs interval. The last row instead compares the
complex plateau means.

All **15 numerical acceptance checks pass**. The maximum trace error is
$4.00\times10^{-15}$, final Hermiticity error is zero, and the smallest final
eigenvalue over the production sweep is $-5.76\times10^{-9}$. This small
negative integration residual is recorded without clipping; the accepted
state-health tolerance is $-10^{-7}$. The small numerical differences in the
logarithmic diagnostic are not evidence of additional physical oscillations.

<p align="center">
  <img src="../figures/task_2_3_validation.png" width="860" alt="Readout controls and numerical comparisons">
</p>

**Linearity and numerical agreement.** (a) Plateau contrast versus drive;
dashes give the leading prediction. (b) $d(t)$ is the largest complex-field
difference between a reference and the production trajectory over both
codewords, divided by the nominal predicted half contrast. The references
check the integration method, tolerance and joint cutoff increase.

~~~bash
pip install -r requirements.txt
python -m tasks.task_2_3
python -m unittest discover -s tests -v
python -m tasks.task_2_3 --plot-only
python -m tasks.task_2_3 --reanalyze
~~~

The script writes [JSON metrics](../results/task_2_3.json), a
[trajectory archive](../results/task_2_3_trajectories.npz), and PNG/PDF figures.
Parameters, library versions, observable ordering, thresholds and source hashes
accompany the results. `--reanalyze` refreshes the summaries, plateau-window
metadata, derived flux and checks together, retaining the original simulation
hashes. Physical parameters and cutoffs must match the archive; references must
cover the required comparison interval. `--plot-only` redraws using archived
parameters. The [notebook](../notebooks/08_task_2_3_readout.ipynb) loads the saved
results by default and can rerun the calculation.

## Measurement interpretation

The coherent signal flux carried by the opposite real fields is
$\kappa_b(\Delta\beta_R/2)^2=0.002311$ photons/µs. It excludes the common field
and incoherent emission, and sets the scale of the coherent readout signal.

The reported time is the turn-on settling time of the conditional **mean**
buffer response. A practical measurement must also integrate a noisy output
record. Detector efficiency, amplifier noise, measurement records and
single-shot classification are outside this master-equation calculation.
Consequently, mean-field contrast does not establish a readout fidelity or an
integration time.

Likewise, the settled values describe local responses during a finite
observation window. Eventual memory-bit switching can erase their initial-state
dependence. The 8-µs check tests plateau stability over that interval; it does
not establish an infinite-time stationary contrast or a protected bit-flip
lifetime. Increasing the readout strength and quantifying that trade-off
belong to Task 2.4.
