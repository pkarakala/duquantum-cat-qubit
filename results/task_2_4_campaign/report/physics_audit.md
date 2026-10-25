# Independent Task 2.4 circuit and logical-definition audit

Scope: read-only audit of `src/circuit.py`, `src/circuit_corrections.py`, `src/readout_optimization.py`, `src/readout_measurement.py`, `tasks/task_2_4.py`, the challenge, and the draft report. No maintained file edited. This source is still changing in another active session; the probe log records SHA256 identities. Numerical probes used the previously validated Python 3.12 environment. Evidence: `circuit_probe.txt` alongside this note.

## Executive conclusion

The declared phase/sign convention, number-dependent exchange and logical projector check correctly. Three claim-level safeguards are essential: corrected idle controls (mean-force cancellation is not exact darkness), identification of the switching eigenmode, and explicit limitations of Hamiltonian-only circuit corrections. The current task module has no executable study entrypoint. Structured numbers and checks are in `auditchecks.json`.

## Findings that check correctly

1. **Cubic sign and phase.** At the challenge bias Delta=+pi/2, Sigma=-pi/2+epsilon_p cos(omega_p t), the Josephson interaction is +2 EJ epsilon_p cos(omega_p t) sin(Phi) at first pump order. Its cubic cross term is negative, giving coefficient -EJ epsilon_p phi_a^2 phi_b/2 for a^2 b† + h.c. A pi pump-phase shift reverses it. The draft explicitly makes this change and chooses the buffer phase consistently. There is no factor-of-two discrepancy in the positive-g2 model.
2. **Separate physical microwave port.** The added lab force 2 epsilon_Z cos(omega_a t+theta)(a+a†) gives epsilon_Z(e^{i theta}a+e^{-i theta}a†) in the rotating frame. A capacitive charge coupling can realize the same convention by phase adjustment. The draft correctly does not derive the memory drive merely by changing the ATS two-photon pump. An independent memory-drive transmission line is present in the primary experiment [Réglade et al., Supplement S2–S4](https://arxiv.org/html/2307.06617v2#S3).
3. **Fifth/seventh/all-phase exchange.** Normal ordering gives the fifth-order factors 1-(phi_a²+phi_b²)/2 -(n-2)phi_a²/3 -m phi_b²/2. The Laguerre expression and fundamental-pump multiplier 2 J1(epsilon_p)/epsilon_p in `exchange_factor` reproduce this expansion. The buffer calibration uses 2 J2(2 phi_a alpha)/(phi_a alpha)², as required for the coherent expectation.
4. **RWA selection.** In units of 0.8 GHz the mode frequencies are (5,6), pump 4. First-pump resonances satisfy 5 Delta_n_a+6 Delta_n_b=±4. The lowest odd-potential process is the desired (-2,+1) transition. Other first-harmonic odd-potential channels first appear at phase order 19. Therefore the sine exchange should be described as all phase orders of the selected two-photon channel, not literally the complete first-harmonic Hamiltonian; the omitted channels are extremely high phase order here. The sixth-phase-order second-order van-Vleck result can indeed be purely diagonal: a two-pump (-4,+2) transition has oscillator degree six, and a commutator lowers polynomial degree by at least two, so it first requires total phase order eight.
5. **Consistent perturbation order and sign.** For H(t)=H_m exp(i m omega t)+h.c., the stated leading correction [H_m,H_m†]/(m omega) has the correct sign. Keeping linear×fifth as well as cubic×cubic at sixth phase order is necessary and is implemented. The first-pump odd potential does not produce a first-order static Kerr at the ideal bias.
6. **Orthonormal code projector.** `logical_projectors` constructs normalized even/odd cats before defining |0_L>,|1_L>. P+M is an actual rank-two orthogonal projector, unlike the naive sum of coherent-state projectors. This agrees with the definition in [Dubovitskii, Eq. (3)](https://arxiv.org/html/2407.17299v2#S2).
7. **Rate convention.** The draft multiplies the literature's symmetric one-way bit-flip rate by two when reporting the observable population-imbalance decay. Its weak-drive prediction Gamma_X,drive≈4 epsilon_Z² exp(-2 alpha²)/(kappa_2 alpha²) is consistent with [Dubovitskii, Table I](https://arxiv.org/html/2407.17299v2#S2.T1), restricted to that paper's adiabatic perturbative model. It is not a quantitatively justified substitute for the full two-mode rate.

## Important scientific limitations / fixes before headline claims

### A. Zero mean buffer force does not restore an exact dark state

`buffer_drive(..., order='sine')` cancels <dot b> at |alpha,0>. The number-dependent exchange operator does not annihilate the entire coherent state. An executed (40,14), alpha=2.1, epsilon_Z=0 check gives

- Cubic: ||H |alpha,0>|| = 1.887e-10 per us (truncation residual).
- Fifth phase order: 0.0532775 per us.
- Seventh: 0.0505727 per us.
- All-phase fundamental: 0.0506322 per us.

The mean buffer derivative is essentially zero in every case. Thus vanishing mean force and coherent dark-state cancellation are different statements. **Fix:** explicitly label the calibration as mean-force cancellation. Include corrected-model no-readout evolution, idle emission/leakage, and a duration-matched idle comparator before attributing all final disturbance to the readout.

### B. The correction scale is substantial on the dissipative timescale

At supplied parameters, sixth-phase-order coefficients are approximately delta_a=5.79582, delta_b=143.714, K_a=-0.0175409, K_b=-9.63496 and chi=-1.43430, all in inverse us (the Kerr coefficients multiply n(n-1), so they are not the alternate half-Kerr convention). K_b is comparable with kappa_b=16.3363. Frequency compensation is therefore a physical additional control/calibration, not harmless relabeling.

The linear off-resonant forcing divided by its smallest detuning is approximately 0.106 for the memory and 0.265 for the buffer. Small epsilon_p=0.0353 alone does not bound rare-switching-rate errors. Hamiltonian-only van-Vleck corrections omit bath micromotion, third/further pump harmonics and, for the all-phase diagonal check, higher-order off-diagonal resonances. **Fix:** treat corrected rates as sensitivity evidence rather than a device error certificate. Validate representative short-time, stroboscopic observables against a direct rotating-frame time-dependent circuit calculation; compare phase-six and all-phase results after identical physical calibration. A Floquet dissipative treatment would be needed for a strong claim about the circuit's exponentially small lifetime.

The proposed junction imbalance is about Delta_EJ/EJ=-0.00881. It cancels the sixth-order cross-Kerr, but it leaves K_a≈-0.00320 and K_b≈-0.67061 per us; higher-order residual interactions remain. A cancellation formula alone is not evidence of improved measured cycles.

### C. Finite-alpha coherent inputs have nonzero initial wrong-logical population

For initial |+alpha> and the orthonormal logical |1_L>, the population is [1-sqrt(1-exp(-4 alpha²))]/2. It is approximately 0.03655 at alpha=0.7, 9.84e-5 at alpha=1.4, and 5.46e-9 at alpha=2.1. The raw final logical population is a valid reported number, but it is not identical to an induced transition probability. **Fix:** save the initial value, report duration-matched idle evolution, or initialize the exact orthonormal logical state in an additional control run. Do not silently relabel coherent-state initialization as exact |0_L>.

### D. A nearest-zero eigenvalue is not automatically the logical switching mode

Both `bit_spectrum` and `corrected_bit_spectrum` currently request k=1 near a shift and report its real decay as Gamma_X. The antisymmetric representation is exact in its stated model, and the corrected full-Hermitian packing is appropriate, but these representation facts do not identify the physical mode. Under strong drives or broken branch symmetry, verify overlap with the actual initial-state difference and the logical population-imbalance observable, track the mode continuously from idle, and compare with independent time-domain decay at tractable alpha. If a pair becomes oscillatory or multiple rates matter, report that the two-state rate model fails. Numerical residual alone cannot certify mode identity.

### E. Homodyne reference has a factor-four convention that must stay explicit

The existing I=eta kappa_b integral (Re Delta_B)² dt equals SNR²/4 under dY=2 sqrt(eta kappa_b) Re(B) dt+dW and the full mean-separation-over-standard-deviation convention. Thus ideal Gaussian error is Phi(-sqrt(I)); I=1 gives 15.9%, as the draft correctly says. Keep I labelled a signal/information reference, or convert to SNR²=4I before using the user's requested SNR notation. The quantum-regression correction is valuable, but stationary boxcar variance is not the covariance of a complete nonstationary pulse or an optimized matched filter.

## Minimal queued experiment checks

1. Cubic, sine, and compensated-correction idle controls at alpha=2.1, matching every readout cycle's total duration; both initial codewords; save code leakage, logical populations, buffer population/emission and trace health.
2. At two representative amplitudes/drives, compare phase-six correction, all-phase diagonal correction and a directly integrated rotating-frame pump over multiple fundamental periods; average/strobe consistently, separately reporting micromotion.
3. Static-drive rates at small alpha with eigenmode overlaps, at least several nearby eigenpairs, shift variation and independent population-imbalance fits. Use physical alpha=2.1 only where the rate is numerically resolved, with cutoff convergence of the rate itself.
4. Corrected and balanced-hardware cycles at the same mean-signal target, including the actual frequency/buffer-drive recalibration and final reset interval. Compare with a tuned constant-drive baseline, not only the old weak readout.
5. For every pulse, report residual population and post-pulse emitted information. Do not count post-pulse photons toward the on-pulse signal target unless the measurement window explicitly includes them.

## Execution blocker in the inspected snapshot

At inspection time `tasks/task_2_4.py` contains helpers only and ends at `cycle_metrics`; no `main` or CLI call launches the study. Running `python -m tasks.task_2_4` would do no simulations. The cloud queue must invoke a tested explicit case manifest or use the completed runner after it is implemented. The draft report contains numerical placeholders and is not a finished deliverable.

Conclusion: no blocking algebraic sign/factor error found in the implemented circuit construction at the stated orders. The present blockers are executable orchestration and the interpretation/validation items above. Do not treat provisional corrected-circuit rare rates or the hardcoded enlargement strategy as validated final findings.
