# Tasks 2.1 and 2.2: bit-flip and phase-flip relaxation

The calculations retain the full supplied memory–buffer Lindblad model, with exchange coupling $g_2=2\pi\times0.763$ µs⁻¹, buffer loss rate $\kappa_b=2\pi\times2.6$ µs⁻¹ and memory loss rate $\kappa_a=2\pi\times0.0093$ µs⁻¹. For every real cat amplitude $\alpha$, set the buffer drive to $\epsilon_d=g_2\alpha^2$. The memory and buffer annihilation operators are $a$ and $b$. The only jump operators are $\sqrt{\kappa_a}a$ and $\sqrt{\kappa_b}b$; thermal excitation, dephasing and additional Hamiltonian terms are absent.

## Rate conventions and initial states

Task 2.1 starts from a coherent memory state and vacuum buffer. Task 2.2 starts from the normalized even cat and vacuum buffer. Initial memory states use normalized Fock expansions at the stated cutoffs; the independent solver uses the same physical initial state. A finite-dimensional displacement exponential gives a slightly different state near the truncation limit, so the comparison explicitly matches the Fock expansion in both solvers. All rates are in µs⁻¹, all saved times in µs, and $\Gamma_X=1/T_X$, $\Gamma_Z=1/T_Z$ follow the challenge's observable-relaxation convention.

For a symmetric classical switching process at rate $r$ in each direction, the population difference decays as $e^{-2rt}$, so the observable rate is $2r$. This factor also appears in parity decay because each photon loss reverses its sign. At small cat amplitudes, coherent codewords overlap; the extracted real-amplitude decay remains well defined but should not be identified with individually observed classical flips.

## Task 2.1 results and exponential scaling

Fit the untransformed real mean amplitude from 2 µs onward:

```math
\mathrm{Re}\langle a(t)\rangle=A\exp[-\Gamma_X(t-t_{\mathrm{fit}})],\qquad t_{\mathrm{fit}}=2\ \mathrm{\mu s}.
```

Symmetry fixes its asymptotic offset at zero. Each trajectory resolves at least one decay time, with horizons chosen from the first-order estimate and capped at 10,000 µs. At the largest amplitude, the measured horizon is 1.202 decay times; the real mean amplitude decreases by about 70% over the simulated interval.

| $\alpha$ | $\Gamma_X$ (µs⁻¹) | $T_X$ (µs) |
|---:|---:|---:|
| 0.7 | 0.00954424 | 104.78 |
| 0.85 | 0.00511995 | 195.31 |
| 1 | 0.00230066 | 434.66 |
| 1.15 | 0.000863556 | 1158.00 |
| 1.3 | 0.000275644 | 3627.87 |
| 1.4 | 0.0001202 | 8319.46 |

Regressing $\log\Gamma_X$ against $\alpha^2$ gives $\Gamma_X=C_Xe^{-\gamma\alpha^2}$, with $C_X=0.04382$ µs⁻¹, $\gamma=2.994$ and $R^2=0.99946$. Removing either endpoint gives exponents 3.042 and 2.963. This finite-interval sensitivity is more informative than a statistical error bar for deterministic, numerically converged trajectories. The approximate exponential law is not asserted as an exact asymptote.

### Direct-overlap estimate

For real $\alpha$, the naive loss matrix element is

```math
\langle-\alpha\rvert a\lvert\alpha\rangle=\alpha e^{-2\alpha^2},\qquad
\Gamma_X^{\mathrm{GR}}\simeq2\kappa_a\alpha^2e^{-4\alpha^2}.
```

The second expression converts a one-way Golden-Rule estimate into the observable decay convention. The coherent states are nonorthogonal, and an individual loss jump leaves a coherent state unchanged apart from its eigenvalue; this matrix element alone is therefore not a complete description of the stabilized open-system dynamics.

A first-order calculation in the orthonormal even/odd cat basis gives

```math
\Gamma_X^{(1)}=\frac{2\kappa_a\alpha^2}{e^{4\alpha^2}-1}.
```

Its large-cat limit agrees with the direct estimate. Even the naive expression, fitted as a pure exponential over the same finite interval, gives exponent 3.087 because of its $\alpha^2$ prefactor. Comparing the numerical exponent directly with four would conflate this prefactor with a change in the exponential dependence.

At $\alpha=1.4$, the direct estimate is 9.017375e-05 µs⁻¹, while the full rate is 0.0001202 µs⁻¹, a 33.30% excess. Reducing the memory loss by factors 2, 4 and 8 reduces that excess. Fitting $\Gamma_X/\kappa_a$ linearly against $\kappa_a$ gives a first-order coefficient 0.001543069, within 0.047% of the ideal cat-space value 0.00154379, and a positive quadratic coefficient 0.008792623 µs. This numerical loss-strength dependence supports a finite-stabilization correction. [Dubovitskii, Phys. Rev. A 111, 012617 (2025)](https://arxiv.org/html/2407.17299v2) derives an additional second-order contribution with $e^{-2\alpha^2}$ dependence in the effective single-mode model. Its single-mode prefactor is not treated as exact for the present two-mode parameters.

### Comparison with the challenge benchmark

The fitted effective exponent is larger than the prompt's approximate $\gamma\lesssim2$ reference. The [experimental model, Eq. S4 and Table S2](https://arxiv.org/html/2307.06617v2#S4.SS3) includes thermal memory and buffer excitation, absent from the challenge model used here. Finite fitting range, the amplitude prefactor and higher-order loss effects also matter. The comparison is therefore qualitative; no thermal channel is added to force agreement with the benchmark.

## Task 2.2 results and linear scaling

Fit parity using a steady offset:

```math
\langle\Pi(t)\rangle=\Pi_\infty+A\exp[-\Gamma_Z(t-t_{\mathrm{fit}})],\qquad
\Pi=(-1)^{a^\dagger a},\quad t_{\mathrm{fit}}=1\ \mathrm{\mu s}.
```

All three parameters are fitted to the untransformed observable. The initial transient is excluded, and each run extends to approximately six nominal decay times. The offset is appreciable for smaller cats: at $\alpha=1.2$, $\Pi_\infty=0.11496$. Fitting zero offset instead underestimates the rate by 45.0% over the same time interval.

| $\alpha$ | $\Gamma_Z$ (µs⁻¹) | $T_Z$ (µs) | Fitted $\Pi_\infty$ |
|---:|---:|---:|---:|
| 1.2 | 0.168535 | 5.9335 | 0.114962 |
| 1.5 | 0.262159 | 3.8145 | 0.0231123 |
| 1.8 | 0.377814 | 2.6468 | 0.00323674 |
| 2.1 | 0.514559 | 1.9434 | 0.000316649 |
| 2.4 | 0.672337 | 1.4873 | 2.04746e-05 |

At the physical target $\alpha=2.1$, the rate is 0.514559 µs⁻¹ and the lifetime 1.9434 µs. The large-cat prediction is $2\kappa_a\alpha^2=0.5153846$ µs⁻¹. A free-intercept regression $\Gamma_Z=m\alpha^2+c_Z$ across all five amplitudes gives slope $m=0.116685$ µs⁻¹ and fitted intercept $c_Z=1.6831e-05$ µs⁻¹, with $R^2=0.99999677$. The slope differs from $2\kappa_a=0.116867$ µs⁻¹ by 0.156%. The through-origin slope is 0.1166895 µs⁻¹. The earlier Task 1.3(a) estimate used vacuum inflation and a zero-offset log fit over 1–6 µs; it differs by 0.215%. Here the memory starts in the even cat and the longer fit explicitly includes steady parity.

### Finite-overlap correction

In the normalized even/odd cat basis, single-photon loss induces rates $\kappa_a\alpha^2\tanh(\alpha^2)$ from even to odd and $\kappa_a\alpha^2\coth(\alpha^2)$ from odd to even. Their sum gives the parity relaxation rate, and their imbalance gives the steady parity:

```math
\Gamma_Z^{(1)}=2\kappa_a\alpha^2\coth(2\alpha^2),\qquad
\Pi_\infty^{(1)}=\operatorname{sech}(2\alpha^2).
```

These first-order formulas explain the nonzero offset and approach $2\kappa_a\alpha^2$ and zero offset for larger cats. The reported numerical fit does not constrain its offset to this approximation. Finite memory loss and the full buffer response remain in the calculation.

## Numerical method and validation

The sparse solver is an exact representation of the finite two-mode equation. A buffer-basis rotation $U=\exp(i\pi n_b/2)$ makes the Hamiltonian imaginary, $H'=iK$, while jump-operator phases leave their dissipators unchanged. The density matrix remains real symmetric for the stated initial states, so its upper triangle suffices. No states are removed beyond the stated Fock cutoffs; no adiabatic elimination or two-cat-state projection is used.

Phase-decay propagation may use the operator-even sector of memory parity conjugation. It includes density-matrix blocks with both even and odd memory photon number, so it fully retains single-photon parity flips. Decay eigenvalues are obtained separately in the operator-odd sector for $\Gamma_X$ and the operator-even sector for $\Gamma_Z$, excluding the stationary eigenvalue.

Radau integration uses relative tolerance $10^{-9}$ and absolute tolerance $10^{-11}$. Tight checks use $10^{-11}$ and $10^{-13}$, respectively, at the amplitude-sweep endpoints and the physical phase-decay target. Independent full Dynamiqs Tsit5 calculations use $10^{-10}$ and $10^{-12}$, respectively, covering 0–100 µs for each bit-flip case and 0–10 µs for each phase-flip case, with directly shared output times. Long-time fits are also checked against the generator's slow decay eigenvalue. Fit-window tests use 2 µs, 10% and 25% of the horizon for bit flips, and 0.5, 1 and 2 µs for parity. Population monitors and trace are checked at every saved time; full-state eigenvalues are checked at five saved states per case.

| Task | Cutoff change | Fit/eigenvalue difference | Dynamiqs rate difference | Fit-window spread | Tight-tolerance rate change |
|---|---:|---:|---:|---:|---:|
| 2.1 | 0.0042411% | 6.2057e-07% | 1.8546e-05% | 6.1696e-07% | 6.5663e-09% |
| 2.2 | 0.00025137% | 4.9167e-06% | 2.5116e-06% | 0.00015186% | 2.2468e-08% |

The cutoff criterion is 0.1% relative rate change against the larger reference. Separate memory/buffer increases are performed at every amplitude. Task 2.1 uses $(20,6)$ and reference $(24,8)$; Task 2.2 uses $(24,8)$ and reference $(28,10)$. These code-state initializations do not undergo the large vacuum-inflation overshoot that required $(32,12)$ in Task 1.1. Every chosen cutoff also passes the 0.1% top-level population criterion. The references are finite numerical calculations; the comparisons do not establish an exact infinite-Hilbert-space bound.

### Task 2.1

| $\alpha$ | Chosen rate (µs⁻¹) | Larger-reference rate (µs⁻¹) | Relative change (%) |
|---:|---:|---:|---:|
| 0.7 | 0.00954424284 | 0.00954424284 | 1.913947e-09 |
| 0.85 | 0.00511994906 | 0.00511994907 | 1.54872e-07 |
| 1 | 0.00230065581 | 0.00230065594 | 5.862457e-06 |
| 1.15 | 0.000863555632 | 0.000863556667 | 0.0001198861 |
| 1.3 | 0.000275644056 | 0.000275647727 | 0.001331829 |
| 1.4 | 0.00012020005 | 0.000120205148 | 0.004241134 |

### Task 2.2

| $\alpha$ | Chosen rate (µs⁻¹) | Larger-reference rate (µs⁻¹) | Relative change (%) |
|---:|---:|---:|---:|
| 1.2 | 0.168535388 | 0.168535387 | 4.000358e-07 |
| 1.5 | 0.262158972 | 0.262158973 | 3.235457e-07 |
| 1.8 | 0.377813591 | 0.377813592 | 3.220585e-07 |
| 2.1 | 0.514558937 | 0.514558824 | 2.191127e-05 |
| 2.4 | 0.672337454 | 0.672335764 | 0.0002513725 |

The largest sampled memory top-two and buffer top-level probabilities are 1.0509e-11 and 4.508e-09 in 2.1, and 3.1895e-07 and 4.6426e-08 in 2.2, expressed as fractions. Maximum trace errors are 4.4409e-15 and 1.5543e-15. The smallest full-state eigenvalues among the five-state checks are -2.1543e-16 and -2.9812e-16; the small negative values are numerical roundoff.

## Reproduction and evidence

```bash
python -m tasks.task_2_1
python -m tasks.task_2_2
python -m unittest tests.test_rates -v
```

Both task commands include their numerical checks and resume matching cached trajectories. Use `--rerun` to recompute or `--plot-only` to redraw delivered data. The local cache `results/task_2_cache/` is ignored by Git. JSON results record every fit, check, physical parameter, solver setting and library version; NPZ archives contain the observables and independent check trajectories.

- [Bit-flip results](../results/task_2_1.json), [trajectories](../results/task_2_1_trajectories.npz), and [walkthrough](../notebooks/06_task_2_1_bit_flips.ipynb).
- [Phase-flip results](../results/task_2_2.json), [trajectories](../results/task_2_2_trajectories.npz), and [walkthrough](../notebooks/07_task_2_2_phase_flips.ipynb).
- [Canonical figure captions](../figures/CAPTIONS.md) and [validation record](../reviews/standard-rates-20261025.md).
