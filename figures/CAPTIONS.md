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

**Weak-drive memory-bit readout.** Both initial memory codewords $\lvert s\alpha\rangle$, $s=\pm1$, evolve independently with a vacuum buffer, $\alpha=2.1$, $(N_a,N_b)=(32,12)$ and the constant drive $\epsilon_Z(a+a^\dagger)$ at $\epsilon_Z/g_2=0.05$. Define $\beta_s=\langle b\rangle_s$. (a) Real buffer fields; dotted lines give the leading estimates $-s\epsilon_Z/(2\alpha g_2)$. (b) Imaginary common field $\beta_{\mathrm{com}}=(\beta_++\beta_-)/2$, compared with the zero-drive control and the leading memory-loss contribution $\kappa_a/(4g_2)$. (c) Real separation $\Delta\beta_R(t)=\mathrm{Re}(\beta_--\beta_+)$ divided by $\Delta_{\mathrm{lin}}=\epsilon_Z/(\alpha g_2)$; dashes show local semiclassical linearization including memory loss. (d) Residual $r(t)$ is the larger complex-field distance from the two 3–4 µs means, divided by $\epsilon_Z/(2\alpha g_2)$. Dotted and dashed guides mark $r=0.01$ and $t_{\mathrm{set}}=0.968$ µs, respectively. Both fields satisfy the criterion from this time through 4 µs. Saved times are 2 ns apart.

## task_2_3_validation

**Readout linearity and numerical checks.** (a) Plateau contrast $\Delta\beta_R=\mathrm{Re}(\bar\beta_--\bar\beta_+)$ from 3–4 µs means versus $\epsilon_Z/g_2$, including zero drive. Dashes give $\epsilon_Z/(\alpha g_2)$. (b) Normalized difference $d(t)=\max_s|\beta_s^{\mathrm{ref}}(t)-\beta_s(t)|/[\epsilon_Z/(2\alpha g_2)]$ at the nominal drive $\epsilon_Z/g_2=0.05$. References are independent QuTiP BDF and tighter Tsit5 integration at the production cutoff $(32,12)$, and a joint cutoff increase to $(40,14)$; all physical parameters are shared. Separate memory/buffer cutoff increases and an 8-µs horizon check are reported in the numerical table.
