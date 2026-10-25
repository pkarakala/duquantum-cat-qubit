# Figure captions

The figures are exported as 300-dpi PNGs and PDFs, with animated GIFs for the Wigner time series. Time is in µs; rates are in µs⁻¹ with the angular-frequency convention of `src/config.py`. The cutoffs $N_a$ and $N_b$ count retained memory and buffer Fock states. Physical parameters and numerical methods are specified in [TECHNICAL.md](../TECHNICAL.md).

## Animated Wigner evolution

| GIF | Simulated interval (µs) | Frames | Frame interval (ns) |
|---|---:|---:|---:|
| [Single-photon loss](task_1_0a_wigner.gif) | 0–1 | 201 | 5 |
| [Effective stabilization](task_1_0c_wigner.gif) | 0–2 | 201 | 10 |
| [Two-mode inflation](task_1_1_wigner.gif) | 0–3 | 301 | 10 |
| [Interference decay](task_1_3a_wigner_fading.gif) | 1–6 | 201 | 25 |
| [Logical-state preparation](task_1_3b_wigner.gif) | 0–2 | 201 | 10 |
| [Enlarge/read/restore](task_2_4_wigner.gif) | 0–10.604 | 304 | ≈35 |

Each frame is computed from a solved state, with the same phase-space coordinates and fixed color scale as the static panels below. The displayed clock is simulated time. GIFs play at 25 frames/s, pause for 0.8 s at each endpoint, and loop. A shared palette keeps colors consistent between frames.

Every Wigner panel and animation marks the phase-space origin with a small cross.

## task_1_0a_photon_number

**Single-photon decay.** Mean occupation $\langle n\rangle$ of an initial coherent state $|\alpha_0=2\rangle$. The numerical solution is compared with $|\alpha_0|^2e^{-\kappa t}$ for $\kappa=2\pi\mathrm{\mu s}^{-1}$. The Hamiltonian detuning has the same value and does not affect the occupation. The single-mode cutoff is $N=30$.

## task_1_0a_wigner

**Phase-space evolution under single-photon loss.** Wigner functions of the state in the single-photon decay calculation at the indicated times. The coordinate $\beta$ is the complex phase-space amplitude, so a coherent state $|\alpha\rangle$ is centred at $\beta=\alpha$. All panels share the scale $-2/\pi\leq W\leq2/\pi$, with $\int W(\beta)\mathrm{d}^2\beta=1$.

## task_1_0b_two_photon_loss

**Parity-preserving two-photon loss.** (a) Mean occupation for an initial coherent state $|\alpha_0\rangle$ with $\alpha_0=2$ under the jump operator $\sqrt{\kappa_2}a^2$. The dashed line is the conserved odd-parity weight $P_{\mathrm{odd}}=(1-e^{-8})/2$, which fixes the asymptotic occupation. (b) Fock probabilities $p_n=\langle n|\rho|n\rangle$ at $t=3$ µs. The cutoff is $N=30$.

## task_1_0c_kappa2_sweep

**Effective two-photon stabilization.** Mean occupation from vacuum, plotted against (a) time and (b) scaled time $\kappa_2t$. Legend values specify $\kappa_2/\kappa_{2,0}$, where $\kappa_{2,0}=4g_2^2/\kappa_b$. The dotted line is $\alpha^2=4.41$. The near collapse in (b) reflects two-photon stabilization; the fixed, nonzero single-photon loss rate prevents exact scaling. The cutoff is $N=30$.

## task_1_0c_wigner

**Cat formation in the effective model.** Wigner functions from vacuum at the nominal rate $\kappa_{2,0}$, at the indicated times. The phase-space coordinate is $\beta=\mathrm{Re}(\beta)+i\mathrm{Im}(\beta)$. All panels use the same normalized Wigner convention and color scale, $-2/\pi\leq W\leq2/\pi$; negative values resolve the interference fringes.

## task_1_1_inflation

**Two-mode inflation and Fock-space occupation.** (a) Memory and buffer occupations at $(N_a,N_b)=(32,12)$; the dashed memory curve uses $(24,6)$ (start). The dotted curve is the effective one-mode prediction, and the horizontal line marks $\alpha^2$. (b) Full-range top-level probabilities over 0–3 µs, in percent: $p_a^{(2)}$ sums the probabilities of memory levels $N_a-2$ and $N_a-1$; $p_b^{(1)}$ is the probability of buffer level $N_b-1$. Solid and dashed curves use the same cutoffs as in (a). The dotted line marks our chosen 0.1% tolerance for convergence checks. The $(24,6)$ buffer peak reaches 4.62%, while both $(32,12)$ monitors remain below the tolerance throughout inflation. The buffer monitor is $n_b=5$ for $N_b=6$ and $n_b=11$ for $N_b=12$.

## task_1_1_wigner

**Memory-state evolution in the two-mode model.** Wigner functions of the reduced memory state $\rho_a=\mathrm{Tr}_b\rho$ at the indicated times, for $(N_a,N_b)=(32,12)$ and an initial vacuum. The coordinate $\beta$ is the complex phase-space amplitude. All panels share the normalized scale $-2/\pi\leq W\leq2/\pi$.

## task_1_1_truncation_log

**Top-level occupation across scales.** The probabilities $p_a^{(2)}$ and $p_b^{(1)}$ defined in the inflation figure, for $(32,12)$ and $(24,6)$ (start), displayed as fractions. The dotted line is the chosen numerical tolerance $p_\mathrm{tol}=10^{-3}$. Values below $10^{-8}$ are omitted from the logarithmic curves; the shaded band marks this unresolved range. Signed solver residuals are retained in the numerical audit, without clipping or smoothing the underlying data.

## task_1_1_numerical_checks

**Integration checks for two-mode inflation.** (a) Memory occupation from baseline and tight adaptive integration and an independent BDF solver. (b) Absolute difference from BDF, including fixed-step Rouchon3 calculations with steps $h=1$ and $0.5$ ns; the latter extends to $0.8$ µs. (c,d) Raw signed estimates of $p_a^{(2)}$ and $p_b^{(1)}$ after $1$ µs. Baseline tolerances are $(\mathrm{rtol},\mathrm{atol})=(10^{-8},10^{-10})$; tight tolerances are $(10^{-10},10^{-12})$. Saved intervals are 10 ns for baseline/BDF and 1 ns for tight integration. Negative population estimates expose numerical residuals. All runs use $(N_a,N_b)=(32,12)$.

## task_1_2_cutoff_sweeps

**Separate memory and buffer cutoff sweeps.** (a,c) Vary $N_a$ at fixed $N_b=14$; (b,d) vary $N_b$ at fixed $N_a=40$. Color gradients identify the varied cutoff. Upper and lower rows show memory and buffer occupations, respectively. Black dashed curves give the $(40,14)$ reference; horizontal dotted lines mark $\alpha^2$. Only the first $1.2$ µs of each $3$ µs vacuum-inflation trajectory is shown. These are the same grid slices used for the peak and steady-occupation convergence plot.

## task_1_2_error_grid

**Joint memory-state convergence.** Axes give the retained memory and buffer dimensions $N_a$ and $N_b$. Blue shading shows maximum trace distance $D_{\max}=\max_t\frac{1}{2}\lVert\rho_a(t)-\rho_{a,\mathrm{ref}}(t)\rVert_1$ relative to $(40,14)$, where $\rho_a$ is the density matrix after tracing out the buffer. Smaller states are zero-padded into the reference basis. Lighter shades mean smaller differences; the color bar is logarithmic in percent, with all values at or below 0.1% sharing the lightest shade. Small circles mark the 36 computed pairs. The black curve marks $D_{\max}=0.01$ (1%); its upper-right side passes this state-distance test. Occupation and top-level-probability criteria are checked separately. The ring marks the chosen cutoff $(32,12)$; the star marks reference $(40,14)$, whose self-distance is zero. Background and contour use the same shape-preserving interpolation; cutoff decisions use computed values. Each maximum covers 301 saved times from 0 to 3 µs.

## task_1_2_convergence

**Transient and steady occupation versus cutoff.** Peak occupation $n_{a,\mathrm{pk}}=\max_t\langle n_a(t)\rangle$ and late-time mean $\bar n_{a,\mathrm{ss}}$ for (a) varying $N_a$ at $N_b=14$ and (b) varying $N_b$ at $N_a=40$. The steady estimate averages the final 20 saved samples, 2.81–3 µs. Dotted lines mark $\alpha^2$. Both sweeps start from vacuum.

## task_1_3a_cat_diagnostics

**Diagnostics of the inflated memory state.** (a) Parity $\langle\Pi\rangle$, $\Pi=(-1)^{a^\dagger a}$; even-cat fidelity $F_+=\langle C_+\rvert\rho_a\lvert C_+\rangle$; and purity $\mathcal{P}=\mathrm{Tr}(\rho_a^2)$. The dashed curve fits parity to $Ae^{-\Gamma t}$ over 1–6 µs, with fitted amplitude $A$ and decay rate $\Gamma=0.513$ µs⁻¹, compared with $2\kappa_a\langle n_a\rangle_{\mathrm{ss}}=0.515$ µs⁻¹. The horizontal guide is $1/2$. (b) Coherent-state matrix element $C=2\lvert\langle\alpha\rvert\rho_a\lvert-\alpha\rangle\rvert$ and mean amplitude $\mathrm{Re}\langle a\rangle$. An equal incoherent mixture gives $C=2e^{-2\alpha^2}$, about 0.00030, because the two coherent states have finite overlap. The normalized even cat is $|C_+\rangle\propto|\alpha\rangle+|-\alpha\rangle$; the simulation starts from vacuum at $(32,12)$.

## task_1_3a_wigner_fading

**Decay of memory-state interference.** Reduced-memory Wigner functions at the indicated times, following inflation from vacuum at $(N_a,N_b)=(32,12)$. The coordinate $\beta$ is the complex phase-space amplitude. All panels use the same normalized color scale, $-2/\pi\leq W\leq2/\pi$, so the declining interference contrast can be compared directly.

## task_1_3b_logical_prep

**Preparation of a selected coherent state.** Fidelity is $F_\alpha=\langle\alpha\rvert\rho_a\lvert\alpha\rangle$. (a) Evolution from $|\beta\rangle_a|0\rangle_b$ for real initial coherent-state amplitude $\beta$. (b) Fidelity at $t=2$ µs after stabilization, compared with the initial overlap $\lvert\langle\alpha\vert\beta\rangle\rvert^2$, for $\beta=\alpha e^{i\phi}$, where $\phi$ is the initial phase error relative to the target. Dotted guides mark $F_\alpha=0.99$. (c) Normalized memory amplitude with a drive $i\varepsilon_1(a^\dagger-a)$ applied over the shaded interval, 0–0.1 µs. The control uses $10(a+a^\dagger)$ in the same interval. $\varepsilon_1$ denotes the memory-drive amplitude in µs⁻¹. For displaced starts, time begins after the idealized pulse. All simulations use $(N_a,N_b)=(32,12)$ and $\alpha=2.1$.

## task_1_3b_wigner

**Stabilization after displacement.** Reduced-memory Wigner functions for the proposed preparation sequence, initialized in $\lvert\beta=1.5\rangle_a\lvert0\rangle_b$ and stabilized toward $\lvert+\alpha\rangle$ at $\alpha=2.1$, $(N_a,N_b)=(32,12)$, including memory single-photon loss. Time begins after the idealized displacement pulse, when two-photon stabilization is enabled; the pulse itself is not simulated. Static panels show the indicated times; the animation uses all 201 reduced-memory states over 0–2 µs at 10-ns spacing. Axes denote the complex phase-space coordinate $\beta$. The fixed color range is $-2/\pi\leq W\leq2/\pi$ in every panel and frame.

## task_2_1_bit_flips

**Bit-flip relaxation and exponential suppression.** Full two-mode dynamics from $\lvert\alpha\rangle_a\lvert0\rangle_b$ at $(N_a,N_b)=(20,6)$. Colors identify $\alpha$; the buffer drive is set to $\epsilon_d=g_2\alpha^2$ for each trajectory. (a) Normalized real memory amplitude; colored curves are integrated trajectories and black dashes are exponential fits from 2 µs onward. The logarithmic time axis resolves the different lifetimes and shows times from 1 µs onward. (b) Fitted relaxation rates $\Gamma_X$ versus $\alpha^2$. The black line is the log-linear fit $C_Xe^{-\gamma\alpha^2}$ over $0.7\leq\alpha\leq1.4$; gray dashes show the direct-overlap estimate $2\kappa_a\alpha^2e^{-4\alpha^2}$. Rates are inverse observable decay times, twice symmetric one-way switching rates in the well-separated-codeword limit.

## task_2_2_phase_flips

**Phase-flip relaxation and cat-size scaling.** Full two-mode dynamics from the even cat $\lvert C_+\rangle_a\lvert0\rangle_b$ at $(N_a,N_b)=(24,8)$, with $\epsilon_d=g_2\alpha^2$. Colors identify $\alpha$. (a) Memory parity $\langle\Pi\rangle$, with $\Pi=(-1)^{a^\dagger a}$; black dashes fit $\Pi_\infty+Ae^{-\Gamma_Z(t-t_{\mathrm{fit}})}$ from $t_{\mathrm{fit}}=1$ µs. The fitted offset $\Pi_\infty$ accommodates the finite steady parity of overlapping codewords. (b) Fitted $\Gamma_Z$ versus $\alpha^2$; the black line is a free-intercept linear regression and gray dashes show $2\kappa_a\alpha^2$ using the supplied memory-loss rate. The physical target $\alpha=2.1$ is included. Cutoff, fitting-window, solver and independent Dynamiqs checks are recorded with the numerical results.

## task_2_3_readout

**Readout signals and settling.** Each memory codeword $\lvert\pm\alpha\rangle$ starts with the buffer in vacuum. The full two-mode model includes both loss channels, $\alpha=2.1$, $(N_a,N_b)=(32,12)$ and $\epsilon_Z=0.05g_2$. (a) Real buffer fields over 0–2 µs; dotted lines show the predicted values $\mp\epsilon_Z/(2\alpha g_2)$. Their opposite signs distinguish the memory states. (b) A linear-scale zoom of the larger distance of the two complex fields from their respective final values. Percentages use the predicted field magnitude $\epsilon_Z/(2\alpha g_2)=0.01190476$; final values average 3–4 µs. The shaded region is within the 1% tolerance. Open circles mark temporary entries followed by renewed excursions above tolerance. The filled orange circle and dashed line mark the final entry, at the first saved time inside tolerance after the last violation: 0.968 µs. Both fields remain inside through 4 µs. Saved times are 2 ns apart.

## task_2_3_validation

**Supporting checks: drive strength and numerical accuracy.** (a) Real-field separation between the two memory states, averaged over 3–4 µs, versus $\epsilon_Z/g_2$. Dashes show the prediction $\epsilon_Z/(\alpha g_2)$. This checks that the chosen weak drive gives approximately proportional response. (b) Largest complex-field difference between each reference calculation and the production result, over both initial memory states, divided by the nominal predicted field magnitude $\epsilon_Z/(2\alpha g_2)$. References use independent QuTiP BDF and tighter Tsit5 integration at $(32,12)$, and a larger $(40,14)$ cutoff. These check that the reported signal and settling are numerically reliable. Separate memory/buffer cutoff increases and an 8-µs run are recorded in the numerical table.

## task_2_4_tradeoff

**Readout signal and bit protection.** (a) Real separation of the two buffer fields, averaged over 3–4 µs, versus memory-drive strength. (b) Observable switching rate $\Gamma_X$. (c) Mean-field information rate $\dot{\mathcal{I}}=\kappa_b(\Delta\beta_R)^2$ versus switching rate. Colors identify target cat amplitude; markers are computed points and connecting lines guide the eye. Grey dotted guides indicate undriven storage at $\alpha=2.1$. Field trajectories use $(32,12)$. The initial $\alpha=2.1$ rate sweep uses $(28,10)$; promoted $\alpha=2.6$ points use $(40,16)$ at $\epsilon_Z/g_2=0.1$ and $(36,16)$ at 0.25. The 0.5 point at $\alpha=2.6$ appears only in (a), since its rate has not received the promoted-point checks. Strong-drive finite-window contrast is not an infinite-time steady signal. Numerical qualifications are given in the [report](../docs/task_2_4_optimization.md).

## task_2_4_protocol

**Enlarge, read, restore.** Conservative cubic-model sequence with storage amplitude $\alpha_0=2.1$, readout amplitude 2.6, two 2-µs quintic ramps, $\epsilon_Z/g_2=0.1$ during the 41.400-µs read interval, and 2 µs of final relaxation. (a) Target $\alpha(t)$ and actual real memory amplitude $\mathrm{Re}A_+(t)$, where $A_s=\mathrm{Tr}(a\rho_s)$. (b) Memory-drive envelope. (c) Real buffer fields for the two independently evolved initial coherent states; solid curves use enlarged readout and dashed curves use the weak reference at fixed $\alpha=2.1$, $\epsilon_Z/g_2=0.05$. (d) Conditional-mean information accumulated through each drive's end; the dotted line is the target $\mathcal{I}=1$. The weak reference uses $(32,12)$ and the conservative cycle uses $(38,16)$. The complete clocks include return and final relaxation. The information functional assumes ideal homodyne shot noise; it is not a classification fidelity.

## task_2_4_validation

**Stored-bit disturbance and numerical comparisons.** (a) Final wrong-logical-state population $p_X$ and code-space leakage $\ell$, as absolute probabilities without postselection. The logical projectors use orthonormal combinations of normalized even and odd cats at $\alpha_0=2.1$. Black mark: directly integrated zero-drive control over the same conservative-cycle clock, at $(28,10)$. (b) Maximum buffer-field differences at shared, exactly saved physical switch times and the final time, divided by the predicted single-pointer magnitude $\beta_{\rm lin}=\epsilon_Z/(2\alpha g_2)$. “Tolerance” compares conservative cycles at $(36,14)$ with $(\mathrm{rtol},\mathrm{atol})=(10^{-10},10^{-12})$ and $(10^{-11},10^{-13})$. “Cutoff” compares $(36,14)$ with $(38,16)$ for that cycle. “QuTiP” compares independent BDF and Dynamiqs integration of the optional fast cycle at identical $(32,12)$ cutoffs. Full-trajectory comparisons and resampling sensitivity are recorded separately. A small field difference does not by itself certify a rare switching rate; rate and final-population cutoff checks are in the report.

## task_2_4_input_shaping

**Less ringing versus accumulated signal.** At fixed $\alpha=2.1$ and peak memory drive $0.05g_2$, compare an abrupt step with a two-step zero-vibration shaper: drive fraction 0.65768 for 0.15931 µs, then full drive. (a) Drive fraction; (b) real buffer-field separation divided by $\Delta_{\rm lin}=0.05/2.1$; (c) conditional-mean information $\mathcal{I}(t)$. Colors are shared across panels. The full complex-field 1% settling time decreases from 0.968 to 0.666 µs, while information at 4 µs decreases by 2.87%. Both branches are independently evolved at $(32,12)$; numerical curves are unsmoothed.

## task_2_4_circuit

**Circuit-model sensitivity.** (a) Real buffer-field separation in the balanced circuit model. Blue: $(\alpha,\epsilon_Z/g_2)=(2.1,0.05)$; orange: $(2.6,0.1)$. Solid curves retain the ATS-pump-only second-pump-order phase-six correction; dashed curves retain the full-phase fundamental-pump van-Vleck matrix and resonant static cosine. All field trajectories use $(32,12)$. (b) Phase-six enlarged-readout switching rates versus memory cutoff, with filled circles at $N_b=10$ and a hollow triangle at $N_b=12$. The dotted guide is matched balanced undriven storage at $(32,10)$. The intentional junction half-difference is $\Delta E_J/E_J=-0.008810$; frequencies and pump resonance are recalibrated. Final memory and separate buffer increments change the driven rate by 2.49% and 4.69%, respectively. Microwave ports use their RWA; mixed pump/control counter-rotating terms are omitted. This is a cutoff-qualified partial-model witness; panel (b) does not give full-phase rates or a device guarantee.

## task_2_4_wigner

**Memory enlargement and return.** Reduced-memory Wigner functions during the optional fast cubic-model cycle: $\alpha_0=2.1$, $\alpha_{\rm ro}=2.6$, $\epsilon_Z/g_2=0.25$, 1-µs ramps, 6.604-µs readout and 2-µs final relaxation. Upper/lower rows start from $|+\alpha_0\rangle$ and $|-\alpha_0\rangle$. Axes give the complex memory phase-space coordinate $\beta$; all panels use the same $-2/\pi\leq W\leq2/\pi$ scale and mark the origin. These visualizations use $(32,12)$; rare errors require the larger-cutoff checks. The [animation](task_2_4_wigner.gif) shows the positive initial state using 304 uniformly spaced solved density matrices over 0–10.604 µs, at approximately 35-ns spacing. No density matrices are interpolated.


## task_2_4_baseline

**Both complex weak-readout pointers.** Full two-mode trajectories at alpha 2.1,
epsilon_Z/g2=.05 and32x12 cutoffs. (a) Opposite real buffer fields, with leading
weak-response predictions as dashed guides. (b) Common imaginary response;
branch curves overlap. The dotted guide is the leading photon-loss offset
kappa_a/(4g2). No trace is smoothed. Reproduce with
`python tools/plot_task_2_4_baseline.py`.

## task_2_4_campaign_synthesis

**Fixed-time signal/error/termination trade-off.** Constant, raised-cosine and
Gaussian pulses share4-us readout,2-us recovery, peak epsilon_Z/g2=.5 and32x12
cutoffs. (a) Conditional-mean shot-noise SNR squared at pulse end (4I).
(b) Worse-branch wrong-logical population after recovery, in percent.
(c) Buffer photons at pulse end, on a log scale. These are common-duration,
common-peak comparisons, not a matched-SNR superiority claim. Reproduce with
`python tools/plot_task_2_4_campaign_synthesis.py`; original job IDs and hashes
are in the final evidence index.


## task_2_4_model_validation

**Mean-signal accuracy does not imply an accurate reset prediction.** The same
2-us build/hold/deplete candidate is evaluated classically and by the full
quantum model at discovery cutoff 24x8. (a) Collected information:1.46713
classical versus1.42318 quantum, about3% difference. (b) Predicted mean-field
photons1.03322e-4, quantum mean-amplitude contribution1.93000e-5 and quantum
total photon population3.61309e-3. Fluctuations account for 99.47% of total
photons. These quantities do not by themselves establish nonclassical photon
statistics. Reproduce the evidence index with `tools/synthesize_task_2_4.py`,
then draw with `tools/plot_task_2_4_model_validation.py`. Exact job IDs,
parameters and raw-trajectory SHA256 are indexed in the final summary.
