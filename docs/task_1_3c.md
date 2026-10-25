# Task 1.3(c): what preparing |+α⟩ costs

Four ways to leave the even cat and land in |0_L⟩ = |+α⟩. Methods (i)–(iii) are two-mode protocols at α = 2.1. Method (iv) is a discussion; it was not simulated. The numerical cost table is empty because the 32×12 production run did not finish before the 10:45 EDT stop. No number below is a stand-in for that run. The intro-track displaced-start result lives in `results/task_1_3b.json` (F(β = α, t = 2 µs) = 0.9999915936048853 at 32×12) and is an anchor for method (i), not a v2 record.

## What we got wrong first

The first plan used ε(a + a†) to tilt inflation toward +α. That drive pushes ⟨a⟩ along the imaginary axis, which is the separatrix between the wells. The antiunitary U = P · e^{iπ b†b} · K leaves the vacuum invariant and forces Re⟨a⟩ ≡ 0 for all t, so the state can never fall into +α. The fix is the real-axis drive ε_x · i(a† − a), which keeps only V = e^{iπ b†b} K and therefore keeps ⟨a⟩ real. The ε(a + a†) curve is a forbidden demo, not a preparation method.

## Methods

(i) **Ideal displacement, then stabilization.** Start in |α⟩ ⊗ |0⟩. That state is a dark state of the two-photon Hamiltonian and of √κ_b b when ε_d = g₂ α². Only κ_a perturbs it. The displacement itself is instantaneous, so the cost is an ideal control, not a pulse.

(ii) **Finite pulse, pump off, then stabilization.** From vacuum, apply ε_x = α/τ with g₂ = ε_d = 0 for τ ∈ {20, 50, 100, 200} ns, then switch the nominal stabilization on. The pulse area is ε_x τ = α. Amplitude damping makes ⟨a⟩(τ) = (2 ε_x / κ_a) (1 − e^{−κ_a τ/2}), short of α by about κ_a τ/4. Pranav's intro drive, left on while the pump is already running, is `pump_on=True`. That is not method (ii): the confinement fights the displacement.

(iii) **Symmetry-biased inflation.** Stabilization on from t = 0, plus ε_x = r g₂ for a short t_off, then the drive off. r = 0 is the even-cat control. Not yet run at the production truncation.

(iv) **Measure and postselect.** Inflate to |C₊⟩, then read Z_L with the Task 2.3 readout (an ε_Z drive and buffer heterodyne). The vacuum symmetry makes the two wells equally likely, so postselection keeps |+α⟩ on half the shots and discards the rest. The cost is the readout time plus the discarded half. A deterministic version needs feed-forward and an X_L gate (a pump-phase flip). That gate was not simulated.

## Cost table

<!-- BEGIN AUTO TABLE -->
Production records were not written. The integrator still needs:

```text
python -m tasks.task_1_3b --methods ideal,pulse --write-table
python -m tasks.task_1_3b --methods biased --write-table
python -m tasks.task_lab_frames
```

`--write-table` is not implemented yet; it must fill only this region from `results/records/t1_3b.*.json`, with `rec:` tokens. Do not paste quick-run numbers here.
<!-- END AUTO TABLE -->

## Calibration, in words

Method (ii) asks for a calibrated memory pulse of area α along +Re, with the pump off, and then the usual stabilization. An area error leaves the state short of the well; stabilization is built to pull a nearby state in. A phase error rotates the kick off the real axis, toward the separatrix. The error that actually ruins the preparation is one that restores a → −a, in particular a purely imaginary kick ε(a + a†).
