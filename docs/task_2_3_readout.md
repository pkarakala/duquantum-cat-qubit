# Task 2.3: transmon-free memory-bit readout

A weak memory drive, $\epsilon_Z=0.05g_2$, produces opposite real buffer fields
from the two memory codewords. Their measured separation is **0.02378968**,
**0.0834% below** the leading linear estimate. The response undergoes damped
oscillation and settles to the defined 1% criterion at **0.968 µs**. These are
conditional mean-field results from the supplied full two-mode Lindblad model;
they describe a finite observation interval, rather than single-shot performance.

## Model and drive convention

The added memory drive is real:

$$
H=H_{2\mathrm{ph}}+\epsilon_Z(a+a^\dagger),\qquad
\epsilon_Z=0.05g_2=0.23970352\ \mathrm{\mu s}^{-1}.
$$

Thus $\epsilon_Z/(2\pi)=38.15$ kHz, twenty times below $g_2/(2\pi)=763$ kHz.
The physical parameters, $\alpha=2.1$, buffer drive, and jump operators
$\sqrt{\kappa_a}a$ and $\sqrt{\kappa_b}b$ are unchanged. Production runs use
$(N_a,N_b)=(32,12)$ and double-precision Tsit5 integration with relative and
absolute tolerances $10^{-10}$ and $10^{-12}$. We separately evolve
$|+\alpha\rangle_a|0\rangle_b$ and $|-\alpha\rangle_a|0\rangle_b$.

The drive gives $d\langle a\rangle/dt=-i\epsilon_Z$ before including the other
Hamiltonian and loss terms, so it displaces the memory along the imaginary
axis. Near $a=s\alpha$, with $s=\pm1$, the two-photon coupling responds as
$a^2-\alpha^2\simeq2s\alpha\delta a$. The same displacement therefore generates
opposite real buffer fields in the two wells. A phase-referenced measurement
of that buffer quadrature can distinguish the memory bit. Prepared memory
codewords are assumed; preparation errors are not included.

## Leading response and the common field

Define $\beta_s(t)=\mathrm{Tr}(b\rho_s(t))$ for the initial memory codeword
$|s\alpha\rangle$, and let $\bar\beta_s$ denote its 3–4 µs mean. The leading
local estimate is

$$
\beta_s\simeq-\frac{s\epsilon_Z}{2\alpha g_2}.
$$

This estimate and the buffer-fluorescence readout mechanism are derived in
[Réglade et al., Supplement S8.5](https://arxiv.org/html/2307.06617v2).
At the selected drive, the predicted real fields are $\mp0.01190476$, with
separation $\Delta_{\mathrm{lin}}=\epsilon_Z/(\alpha g_2)=0.02380952$.

The full complex fields need not be negatives of each other. For this
real-parameter model, the antiunitary transformation
$\rho\mapsto\Pi_a\Pi_b\rho^*\Pi_b\Pi_a$, with $\Pi_a$ and $\Pi_b$ the mode
parities, maps the two initial conditions into each other while leaving the
evolution invariant. Consequently,

$$
\beta_-(t)=-\beta_+^*(t).
$$

Their real parts are opposite, while their imaginary parts are equal. Both
codewords are evolved independently to check this relation. We define the
time-dependent separation $\Delta\beta_R(t)=\mathrm{Re}(\beta_-(t)-\beta_+(t))$,
its plateau contrast $\Delta\beta_R=\mathrm{Re}(\bar\beta_--\bar\beta_+)$,
and the common field
$\beta_{\mathrm{com}}(t)=(\beta_+(t)+\beta_-(t))/2$.

Memory amplitude damping explains a leading common imaginary response. The
exact first-moment equations are

$$
\frac{d\langle a\rangle}{dt}
=-2ig_2\langle a^\dagger b\rangle-i\epsilon_Z
-\frac{\kappa_a}{2}\langle a\rangle,\qquad
\frac{d\langle b\rangle}{dt}
=-ig_2(\langle a^2\rangle-\alpha^2)-\frac{\kappa_b}{2}\langle b\rangle.
$$

Replacing moments by products and linearizing about $a=s\alpha$, $b=0$, with
$G_s=2sg_2\alpha$, gives

$$
\delta\dot a=-\frac{\kappa_a}{2}\delta a-iG_s\delta b-i\epsilon_Z
-\frac{\kappa_a s\alpha}{2},\qquad
\delta\dot b=-iG_s\delta a-\frac{\kappa_b}{2}\delta b.
$$

The resulting local stationary buffer field is

$$
b_{s,\mathrm{loc}}=
\frac{-\epsilon_ZG_s+i\kappa_as\alpha G_s/2}
{G_s^2+\kappa_a\kappa_b/4}.
$$

To leading order in memory loss, its imaginary part is
$\kappa_a/(4g_2)=0.00304718$, independent of the well sign. A zero-memory-drive
control distinguishes this common field from the real readout signal.

## Transient and settling definition

The local semiclassical eigenvalues are

$$
\lambda_\pm=-\frac{\kappa_a+\kappa_b}{4}
\pm i\sqrt{(2g_2\alpha)^2-\left(\frac{\kappa_b-\kappa_a}{4}\right)^2}.
$$

The supplied parameters give an underdamped response, approximately a
0.319-µs oscillation period and a 0.244-µs envelope time. The closed-form local
step response is checked against a matrix-exponential solution in the tests.
This factorized approximation guides interpretation; the full quantum
simulation retains higher moments and need not have the same transient shape.

We simulate 0–4 µs and save every 2 ns. Adaptive integration steps are distinct
from these save times. Each branch's plateau estimate $\bar\beta_s$ is its
complex mean over 3–4 µs. Define the normalized complex-field residual

$$
r(t)=\frac{\max_{s=\pm}|\beta_s(t)-\bar\beta_s|}
{\epsilon_Z/(2\alpha g_2)}.
$$

The settling time $t_{\mathrm{set}}$ is the first saved time after which **$r(t)\leq0.01$**
at every remaining sample through 4 µs. This uses both quadratures and excludes
early threshold crossings followed by further ringing. An 8-µs run tests the
plateau and settling time against a later 7–8 µs mean. The zero-drive control
has no signal-relative settling time, represented by JSON null.

## Numerical results

At the nominal drive, the two plateau fields are

$$
\bar\beta_+=-0.01189484+0.00311514i,\qquad
\bar\beta_-=+0.01189484+0.00311514i.
$$

The real separation is **0.02378968**, only **0.0834% below** the leading
estimate. The common imaginary field is retained, rather than counted as
readout contrast. With no memory drive, both branches instead give
$\bar\beta=0.00304907i$ and zero real separation.

| $\epsilon_Z/g_2$ | Real separation | Leading estimate | Relative difference | 1% settling (µs) |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | — | — |
| 0.025 | 0.01189512 | 0.01190476 | −0.0810% | 0.976 |
| **0.050** | **0.02378968** | **0.02380952** | **−0.0834%** | **0.968** |
| 0.100 | 0.04757483 | 0.04761905 | −0.0929% | 0.966 |

The contrast per unit drive varies by just 0.0119% over the nonzero sweep.
This supports the conservative drive choice within the supplied model; it is
not an optimization of measurement speed or induced errors.

The approach is **oscillatory**, with a first contrast maximum at 0.158 µs,
44.3% above the measured plateau, and an approximately 0.313-µs peak-spacing
period. Both complex fields remain within the 1% criterion from **0.968 µs**
through 4 µs; the last crossing lies in **[0.966, 0.968] µs**. The tighter
1-ns output grid gives the same settling time. Using the extended run's
7–8 µs plateau also gives 0.968 µs.

<p align="center">
  <img src="../figures/task_2_3_readout.png" width="860" alt="Conditional buffer fields and settling">
</p>

**Buffer response at $\epsilon_Z/g_2=0.05$.** (a) Real fields from the two
initial codewords; dotted lines mark the leading estimates. (b) Common
imaginary field, its zero-drive control, and the leading memory-loss estimate.
(c) Transient real separation divided by $\Delta_{\mathrm{lin}}$, compared
with the local semiclassical response. (d) Residual $r(t)$; dotted and dashed
lines mark the 1% criterion and $t_{\mathrm{set}}=0.968$ µs, respectively.

At 4 µs, the signed real memory amplitude divided by $\alpha$ is 0.99916 and
the fidelity with the initial coherent codeword is 0.99986, for either branch.
The coherent **signal** flux associated with the opposite real fields is
$\kappa_b(\Delta\beta_R/2)^2=0.002311$ photons/µs. This excludes the common
field and incoherent emission, and does not determine a measurement fidelity.

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

The script writes [finite JSON metrics](../results/task_2_3.json), a
[trajectory archive](../results/task_2_3_trajectories.npz), and PNG/PDF figures.
The archive contains complex means, populations, boundary monitors, codeword
fidelities, and the cutoff/solver/reference comparison trajectories.
Configuration, library versions, observable ordering and source hashes are
stored in the JSON. Reanalysis retains the original simulation hashes and
adds the analysis revision's hashes. It refreshes the plateau-window metadata,
all derived quantities and validation together. Physical parameters and reference
cutoffs must match the archive, and comparison trajectories must cover the full
required time interval; incomplete references are rejected. The
[notebook](../notebooks/08_task_2_3_readout.ipynb) loads
these results by default and can rerun the calculation. Plot-only mode uses the
archived parameters, so changing the current configuration does not relabel
old results as a new experiment.

## Measurement interpretation

The reported time is the turn-on settling time of the conditional **mean**
buffer response. A practical measurement must also integrate a noisy output
record. Detector efficiency, amplifier noise, measurement records and
single-shot classification are outside this master-equation calculation.
Consequently, mean-field contrast does not establish a readout fidelity or an
integration time. The small coherent signal photon flux is reported to keep
its scale explicit.

Likewise, the settled values describe local responses during a finite
observation window. Eventual memory-bit switching can erase their initial-state
dependence. The 8-µs check tests plateau stability over that interval; it does
not establish an infinite-time stationary contrast or a protected bit-flip
lifetime. Increasing the readout strength and quantifying that trade-off
belong to Task 2.4.
