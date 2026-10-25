<!-- Generated from task_2_4_final.md by tools/export_task_2_4_markdown.py. -->

# Readout by temporarily enlarging a stabilized cat

DuQuantum 2026 Alice & Bob challenge: Task 2.4(a-d) · 25 October 2026

[Part (a)](#task-24a-derive-the-readout-hamiltonian) · [Part (b)](#task-24b-establish-the-contrast-error-trade-off) · [Part (c)](#task-24c-propose-and-demonstrate-one-protocol) · [Part (d)](#task-24d-explain-and-validate-the-improvement) · [Supporting appendices](task_2_4_appendices.md)

The goal is to read the memory bit faster while retaining its protection against unwanted switching. We test **enlarge, measure, restore**: increase the cat amplitude from 2.1 to 2.6, apply a stronger memory drive, then return to storage. In the ideal two-mode model, the complete cycle reaches the same calculated signal target in **47.40 µs instead of 110.22 µs** for the specified weak reference. Its estimated readout-stage relaxation rate is below undriven storage, and its final wrong-state population is smaller than the weak reference's.

## Task 2.4(a): derive the readout Hamiltonian

### Pumped circuit and two-photon exchange

With $`\hbar=1`$, the circuit Hamiltonian is

```math
H_{\mathrm{circuit}}=\omega_a a^\dagger a+\omega_b b^\dagger b
-2E_J\cos\varphi_\Sigma\cos(\hat\varphi+\varphi_\Delta),\qquad
\hat\varphi=\varphi_a(a+a^\dagger)+\varphi_b(b+b^\dagger).
```

The operators $`a`$ and $`b`$ annihilate memory and buffer photons; $`\varphi_a`$ and $`\varphi_b`$ are their zero-point phases. At $`\varphi_\Delta=\pi/2`$ and $`\varphi_\Sigma=-\pi/2+\epsilon_p\cos\omega_pt`$, the identities $`\cos(\hat\varphi+\pi/2)=-\sin\hat\varphi`$ and $`\cos\varphi_\Sigma\simeq\epsilon_p\cos\omega_pt`$ give

```math
H_{\mathrm{ATS}}(t)\simeq2E_J\epsilon_p\cos\omega_pt
\left(\hat\varphi-\frac{\hat\varphi^3}{6}+\frac{\hat\varphi^5}{120}+\cdots\right).
```

The mixed cubic contribution is

```math
H_{\mathrm{ATS}}^{(3)}\supset-E_J\epsilon_p\varphi_a^2\varphi_b\cos\omega_pt
(a+a^\dagger)^2(b+b^\dagger).
```

Here $`(a+a^\dagger)^2=a^2+a^{\dagger2}+2a^\dagger a+1`$. In the rotating frame, $`a^2b^\dagger`$ acquires $`e^{-i(2\omega_a-\omega_b)t}`$. Choosing $`\omega_p=2\omega_a-\omega_b`$ cancels that rotation through one pump harmonic. The factor $`1/2`$ from the cosine gives

```math
H_{\mathrm{ex}}=g_2(a^2b^\dagger+a^{\dagger2}b),\qquad
|g_2|=\frac{E_J\epsilon_p\varphi_a^2\varphi_b}{2}.
```

This pump phase gives negative exchange. We shift it by $`\pi`$ and use $`g_2>0`$ throughout. For $`(\omega_a,\omega_b,\omega_p)/2\pi=(4.0,4.8,3.2)`$ GHz, $`E_J/2\pi=40`$ GHz, $`\varphi_a=0.06`$ and $`\varphi_b=0.30`$, the rounded $`\epsilon_p=0.035`$ gives $`|g_2|/2\pi=0.756`$ MHz. Using $`\epsilon_p=0.0353241`$ gives the specified 0.763 MHz. These are illustrative circuit parameters [1,3].

### Separate microwave drives

The flux pump creates the exchange interaction. A separate resonant buffer microwave supplies $`H_d=-\epsilon_d(b+b^\dagger)`$ and sets $`\alpha^2=\epsilon_d/g_2`$. A further memory microwave port supplies the readout force. With the explicit laboratory phase convention

```math
H_{Z,\mathrm{lab}}=2\epsilon_Z(t)\cos(\omega_at-\phi)(a+a^\dagger),
```

the resonant rotating-frame term is $`H_Z=\epsilon_Z(t)(e^{i\phi}a^\dagger+e^{-i\phi}a)`$. The discarded terms rotate at $`2\omega_a`$. A charge-coupled port realizes the same convention after a carrier-phase choice. All main calculations use $`\phi=0`$, giving

```math
\boxed{H=g_2(a^2b^\dagger+a^{\dagger2}b)-\epsilon_d(b+b^\dagger)
+\epsilon_Z(t)(a+a^\dagger).}
```

The memory drive is therefore an explicitly added physical control, rather than an automatic consequence of the specified ATS pump.

### Corrections to the leading interaction

The first-order linear terms are off resonance at the supplied frequencies. Keeping the resonant exchange through fifth order gives

```math
\begin{aligned}
H_{\mathrm{ex}}^{(\le5)}={}&g_2[1-(\varphi_a^2+\varphi_b^2)/2]a^2b^\dagger\\
&-\frac{g_2\varphi_a^2}{3}a^\dagger a^3b^\dagger
-\frac{g_2\varphi_b^2}{2}a^2b^{\dagger2}b+\mathrm{h.c.}
\end{aligned}
```

The last two terms still exchange two memory photons for one buffer photon, but their amplitudes depend on occupation. The first term includes the associated correction to the cubic coefficient. An odd sine potential gives no static Kerr term at first pump order. Off-resonant processes can generate frequency shifts and Kerr interactions at second pump order; those are effective corrections, not terms retained directly by the first-order rotating-wave approximation. [Appendix A](task_2_4_appendices.md#appendix-a-circuit-corrections) derives and tests these corrections. The numerical protocol below uses the leading cubic model: the buffer drive controls cat size, and the memory drive produces the readout signal.

## Task 2.4(b): establish the contrast-error trade-off

### Model and weak-drive response

We solve both modes, with time in µs and angular frequencies in $`\mu\mathrm{s}^{-1}`$:

```math
\dot\rho=-i[H,\rho]+\kappa_a\mathcal D[a]\rho+\kappa_b\mathcal D[b]\rho,
\qquad\mathcal D[c]\rho=c\rho c^\dagger-\tfrac12\{c^\dagger c,\rho\}.
```

The supplied values are $`g_2/2\pi=0.763`$ MHz, $`\kappa_b/2\pi=2.6`$ MHz and $`\kappa_a/2\pi=9.3`$ kHz, with storage amplitude $`\alpha=2.1`$. Because $`g_2/\kappa_b=0.2935`$ and $`\epsilon_d/\kappa_b=1.2942`$, eliminating the buffer is not uniformly justified. Each simulation starts separately in $`|+\alpha\rangle_a|0\rangle_b`$ or $`|-\alpha\rangle_a|0\rangle_b`$.

For $`A=\langle a\rangle`$ and $`B=\langle b\rangle`$, factorization gives

```math
\dot A=-2ig_2A^*B-i\epsilon_Z-\kappa_a A/2,\qquad
\dot B=-i(g_2A^2-\epsilon_d)-\kappa_bB/2.
```

Without memory loss or readout, $`A=\pm\alpha`$ and $`B=0`$: the buffer drive and conversion amplitude cancel. The readout force first moves the memory in its imaginary direction and disturbs that cancellation. Linearize around $`A=s\alpha+\delta A`$, $`s=\pm1`$. Neglecting loss and quadratic deviations, the settled memory equation is $`0=-2ig_2s\alpha B_s-i\epsilon_Z`$, hence

```math
\boxed{B_s\simeq-s\frac{\epsilon_Z}{2\alpha g_2},\qquad
C_b\equiv|B_+-B_-|\simeq\frac{|\epsilon_Z|}{\alpha g_2}.}
```

The buffer fields have opposite real signs. This weak-drive approximation applies after fast settling and before switching erases the initial-bit signal; the driven memory need not remain exactly at $`\pm\alpha`$.

Output distinguishability dephases a superposition, even without switching its bit. Unwanted switching is a separate process: drive-induced excitation can relax into the opposite logical branch.

### Increasing the drive at fixed cat size

Here $`\Gamma_X`$ is the logical population-imbalance decay exponent; a symmetric one-way switching rate is $`\Gamma_X/2`$. We estimate it from the Lindblad generator and check it against time evolution where decay is resolvable ([Appendix B](task_2_4_appendices.md#appendix-b-definitions-and-numerical-validation)).

At $`\alpha=2.1`$, the executed two-mode sweep gives:

| $`\epsilon_Z/g_2`$ | Real-field contrast $`C_b`$ | $`\Gamma_X`$ ($`\mu\mathrm{s}^{-1}`$) |
|--:|--:|--:|
| 0.05 | 0.02379 | $`6.12\times10^{-6}`$ |
| 0.10 | 0.04757 | $`2.37\times10^{-5}`$ |
| 0.25 | 0.11885 | $`1.62\times10^{-4}`$ |
| 0.50 | 0.23689 | $`9.24\times10^{-4}`$ |
| 1.00 | 0.46037 | $`8.61\times10^{-3}`$ |

Over this sweep, a stronger drive produces a larger signal and a larger switching rate. These are static rates: they do not by themselves determine the error of a shorter measurement. A finite protocol must also be tested through its complete return and recovery.

![Fixed-size readout trade-off at $`\alpha=2.1`$. Left: real buffer-field separation averaged over 3-4 µs, with the weak-drive prediction as a dashed guide. Right: estimated logical relaxation rate and the undriven-storage reference. Fields use $`(32,12)`$ cutoffs, rate-sweep points $`(28,10)`$, and the idle guide $`(32,12)`$.](../figures/task_2_4_drive_tradeoff.png)

**Figure 1.** Fixed-size readout trade-off at $`\alpha=2.1`$. Left: real buffer-field separation averaged over 3-4 µs, with the weak-drive prediction as a dashed guide. Right: estimated logical relaxation rate and the undriven-storage reference. Fields use $`(32,12)`$ cutoffs, rate-sweep points $`(28,10)`$, and the idle guide $`(32,12)`$.

## Task 2.4(c): propose and demonstrate one protocol

### Objective and comparison

The fixed-size sweep suggests changing the protection during readout, rather than only increasing the force. Larger cat separation suppresses switching [2], but reduces the weak-drive response as $`1/\alpha`$. We therefore test a larger cat with a stronger drive: $`\alpha=2.6`$ and $`\epsilon_Z=0.1g_2`$.

The objective is a shorter complete cycle at a common signal target, with the estimated readout-stage $`\Gamma_X`$ no larger than **undriven storage at $`\alpha=2.1`$**. Speed is compared with the specified **weak readout at $`\alpha=2.1`$ and $`\epsilon_Z=0.05g_2`$**.

For the model's opposite real buffer responses, use ideal detection efficiency and the fixed real quadrature:

```math
\mathcal I(T)=\kappa_b\int_0^T[\mathrm{Re}(B_+-B_-)]^2dt,
\qquad \mathrm{SNR}^2=4\mathcal I.
```

This is a conditional-mean signal reference with unit white noise and optimal temporal weighting. Both protocols target $`\mathcal I=1`$: a 15.9% ideal coherent-Gaussian classification error, not a demonstrated single-shot fidelity. The general measurement convention is in [Appendix B](task_2_4_appendices.md#appendix-b-definitions-and-numerical-validation).

### Pulse sequence

Keep $`g_2`$ fixed and control cat size through the buffer microwave, $`\epsilon_d(t)=g_2\alpha(t)^2`$:

1. Enlarge $`\alpha:2.1\to2.6`$ over 2 µs, with memory readout off.
2. Apply $`\epsilon_Z=0.1g_2`$ and collect the buffer output for 41.3997 µs.
3. Turn off readout and restore $`\alpha=2.1`$ over 2 µs.
4. Wait 2 µs, then evaluate the original storage logical states.

The two ramps use $`s(u)=10u^3-15u^4+6u^5`$, $`0\le u\le1`$. The readout duration is chosen for the signal target; emission after that interval is excluded from the target. All ramps and recovery count in the complete-cycle time. The weak reference keeps $`\alpha=2.1`$ throughout and has the same 2-µs recovery.

![The selected controls and signal target. Left: the target cat amplitude (black, controlled by the buffer drive) and memory readout drive (orange, right axis). Right: counted information from saved trajectories. Dashed segments show return/recovery time after the measurement window; later emitted information is excluded. Markers give the complete-cycle durations.](../figures/task_2_4_protocol_summary.png)

**Figure 2.** The selected controls and signal target. Left: the target cat amplitude (black, controlled by the buffer drive) and memory readout drive (orange, right axis). Right: counted information from saved trajectories. Dashed segments show return/recovery time after the measurement window; later emitted information is excluded. Markers give the complete-cycle durations.

## Task 2.4(d): explain and validate the improvement

### Complete-cycle results

We evaluate the memory in its original storage basis after recovery. The reported $`p_X`$ is population in the opposite logical state, without postselection; leakage is population outside the orthonormal cat code space ([Appendix B](task_2_4_appendices.md#appendix-b-definitions-and-numerical-validation)). These are directly integrated final populations, not a static rate multiplied by pulse duration.

| Quantity | Weak reference | Enlargement cycle |
|:--|--:|--:|
| Information at measurement end | 1.0000000 | 0.9999925 |
| Readout interval (µs) | 108.2205 | 41.3997 |
| Complete-cycle time (µs) | 110.2205 | 47.3997 |
| Final wrong-logical population $`p_X`$ | $`3.3063\times10^{-4}`$ | $`7.9483\times10^{-6}`$ |
| Final code-space leakage | $`8.110\times10^{-6}`$ | $`8.110\times10^{-6}`$ |

The enlargement cycle is **2.33 times faster at the same calculated signal target**, with a smaller recovered wrong-state population. This comparison includes its extra control time and tests whether the benefit survives return to the original cat size.

### Why it works, and whether protection survives

Doubling $`\epsilon_Z`$ while increasing $`\alpha`$ from 2.1 to 2.6 predicts a field gain $`2(2.1/2.6)=1.615`$. The quantum value is 1.616, and the information accumulation rate increases by 2.61. After both ramps and the common 2-µs recovery are included, the complete-cycle speed gain is 2.33.

The separate static-rate test gives $`\Gamma_X=2.0351\times10^{-7}\,\mu\mathrm{s}^{-1}`$ on the enlarged readout plateau, compared with $`3.8475\times10^{-7}`$ for original undriven storage. The readout value is **0.529 times storage**, meeting the stated protection criterion. That rate test describes the plateau; the complete-cycle population test above also includes switching transients, the ramps and recovery. A separate equal-duration idle comparison is retained in [Appendix B](task_2_4_appendices.md#appendix-b-definitions-and-numerical-validation).

### What the evidence supports

The observed gains exceed the tested cutoff changes. The last cycle-cutoff increment changes $`p_X`$ by 0.775%; the last separate memory and buffer increments change the estimated static rate by 0.699% and 0.530%, with an earlier joint increment of 2.117%. These are empirical convergence checks, not rigorous error bars. [Appendix B](task_2_4_appendices.md#appendix-b-definitions-and-numerical-validation) gives the full cutoff and independent-solver evidence.

The result is a demonstrated improvement over the specified weak reference **within the ideal cubic two-mode model**. It is not a global optimum over all controls. The circuit corrections in [Appendix A](task_2_4_appendices.md#appendix-a-circuit-corrections) have separate static and short-time checks, but the complete enlargement cycle has not been validated with them. Actual single-shot fidelity also remains untested. Additional pulse studies are supporting material in [Appendix C](task_2_4_appendices.md#appendix-c-additional-controls-and-diagnostic-checks).

## AI-assistance disclosure

AI agents assisted with the circuit derivation, code, candidate design, numerical execution, independent audits and report synthesis. Independent implementations, saved trajectories, explicit convergence checks and adversarial review were used to test the results. This disclosure follows the challenge's allowance for AI-assisted code and explanation; it does not substitute for the submitting team's ability to explain and defend the work. No claim of human scientific approval is implied.

## References

1. DuQuantum 2026 Alice & Bob challenge, supplied prompt v4, Task 2.4 and provided tutorials. Local source: `docs/challenge_prompt_v4.md`.
2. K. S. Dubovitskii, *Bit-flip errors in dissipative cat qubits: Second-order perturbation theory*, Physical Review A 111, 012617 (2025). [Primary manuscript](https://arxiv.org/html/2407.17299v2). Context for leakage-mediated errors; not a replacement for the present two-mode calculations.
3. U. Réglade et al., *Quantum control of a cat-qubit with bit-flip times exceeding ten seconds* (2024). [Primary manuscript and supplementary derivations](https://arxiv.org/html/2307.06617v2). Context for ATS pumping, semiclassical dynamics and calibration.

4. R. Gautier, M. Mirrahimi and A. Sarlette, *Designing High-Fidelity Zeno Gates for Dissipative Cat Qubits*, PRX Quantum 4, 040316 (2023). [Primary manuscript](https://arxiv.org/abs/2303.00760). Prior analysis of buffer-mediated logical information and gate errors.
