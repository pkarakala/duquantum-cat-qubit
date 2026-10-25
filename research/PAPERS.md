# Papers we rely on (Section 2)

What we took from each and where it shows up. "Checked" means we compared a number from it against our own simulation.

| Paper | What we use | Where | Status |
|---|---|---|---|
| U. Réglade, A. Bocquet *et al.*, "Quantum control of a cat qubit with bit-flip times exceeding ten seconds," arXiv:2307.06617 | Model, parameters (Table S2); readout ⟨b⟩_ss = ∓ε_Z/(2αg₂) (Eq. S17); measurement-induced dephasing 2ε_Z²/(κ₂α²) (Eq. S18); experimental γ ≈ ln 4.2 | 2.1, 2.3, 2.4 | ⟨b⟩_ss checked (readout.py, linear vs simulated within 1–3% at ε_Z ≤ g₂) |
| M. Mirrahimi *et al.*, "Dynamically protected cat-qubits," arXiv:1312.2017 | Two-photon dissipation L₂ = √κ₂(a² − α²), code space | 2.1, 2.2 | background |
| R. Lescanne *et al.*, "Exponential suppression of bit-flips in a qubit encoded in an oscillator," arXiv:1907.11729 | Experimental Γ_X ∝ e^{−γα²} saturation; buffer-mode architecture | 2.1 | background |
| J. Guillaud, M. Mirrahimi, "Repetition cat qubits for fault-tolerant quantum computation," arXiv:1904.09474 | Why the X/Z bias matters | intro of README | background |
| R. Gautier, A. Sarlette, M. Mirrahimi, "Combined dissipative and Hamiltonian confinement of cat qubits," arXiv:2112.05545 | Bit-flip formula with two exponents (Eq. 4): κ₁α²e^{−4α²} + κ_l e^{−2α²}; thermal channel | 2.1 channels | channel-1 formula checked vs one-mode eigenvalue (96% at α = 1) |
| K. Dubovitskii, "Bit-flip errors in dissipative cat qubits" (arXiv:2407.17299, via Harshit's RESEARCH.md) | Out-of-code-space channel (κ₁²/2κ₂)e^{−2α²} per direction; ε² growth of flips under a drive | 2.1, 2.4b | channel-2 prefactor c ≈ 1.2–1.3 fitted; ε_Z² law seen in one-mode spectra |
| Marquet *et al.* (arXiv:2403.07744, via research thread) | Adiabaticity breaks when κ_b < 8g₂α (underdamped buffer) | 2.3 ringing | ring at 3.2 MHz, Q ≈ 2.05 measured vs 2.46 linear |
| D. T. McClure *et al.*, "Rapid driven reset of a qubit readout resonator" (CLEAR pulses), arXiv:1503.01456 | Pulse shaping against a ringing readout mode | 2.4c pulse families | idea only |
| A. Joshi, K. Noh, Y. Y. Gao, "Quantum information processing with bosonic qubits in circuit QED," arXiv:2008.13471 | Review / notation | background | background |
| dynamiqs documentation (v0.3.7), www.dynamiqs.org | mesolve, pwc pulses, jax.grad through the solver | all | API checked in RESEARCH.md §2 |

Classical methods borrowed: sparse shift-invert Arnoldi (ARPACK via scipy) for the Liouvillian gap; linear-systems
response and SVD for the optimal readout pulse (the matched-filter / optimal-input problem of control theory).
