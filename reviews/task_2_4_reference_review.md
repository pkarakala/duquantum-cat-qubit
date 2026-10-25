# Task 2.4: review of the supplied (a-b) reference and final rewrite

## Assessment

The reference has a useful derivation order: circuit bias, cubic term, resonance,
physical drive, then contrast and error mechanisms. That structure is clearer
than leading with a broad survey of optimization studies. Its repeated preliminary
caveats and separate conclusions are unnecessary in a final submission once
executed evidence is available. The final main answer now follows (a)-(d) in six
pages; detailed support is retained in explicitly labeled appendices.

## What was borrowed, corrected or excluded

| Reference item | Assessment | Final treatment |
|:--|:--|:--|
| A.1-A.3: bias, mixed cubic term, operator rotation | Correct and clearly sequenced | Borrow the step-by-step derivation, including the cosine factor 1/2 |
| A.3: 0.756 MHz versus 0.763 MHz | Correct rounding explanation | Retain; the exact illustrative pump is 0.0353241 rad |
| A.3: exchange sign | Correctly notes convention dependence, but the printed phase fixes a negative sign | State the pi pump-phase shift explicitly before using positive g2 |
| A.4: separate memory and buffer drives | Correct and necessary | Keep both physical ports and their roles explicit |
| A.4: general drive phase | Valid if tied to its laboratory carrier phase | Use cos(omega*t-phi) and epsilon(exp(i*phi)a†+exp(-i*phi)a), matching the code; the reference uses the opposite phase label |
| A.5: fifth-order exchange terms | Correct relative coefficients after a consistent pump-phase choice | Retain both number-dependent terms and the correction to the leading coefficient |
| B.1: written driven Hamiltonian | Omits the buffer drive if H2ph means only the exchange defined in A.3 | Always write the full Hamiltonian including -epsilon_d(b+b†) |
| B.2-B.3: dark cancellation and weak response | Correct under the stated linearization | Retain the short derivation; specify post-settling, pre-switching validity |
| B.4: 0.02 and 0.20 contrast points | Explicitly unverified in the supplied text | Do not import their numerical values; use saved repository trajectories |
| B.6: alpha 0.9 fitted rates and code populations | No corresponding executed evidence supplied with the reference | Exclude; do not extrapolate those proxies to alpha 2.1 |
| B.5: fitting Re<a> under drive | Correct caution | Use the existing physically loaded Liouvillian mode and independently checked time traces; keep the global-mode limitation |
| B.8: kappa_b|DeltaB|²/2 | Correct coherent-output coherence-decay exponent | Include as dephasing under coherent-field and Markov-loss assumptions, not a one-way logical bit-flip rate |
| B.10: target-cat trade-off still unestablished | Describes the reference's preliminary evidence, not the repository's later executed work | Replace with actual target-cat rate estimates and explicit convergence/mode qualifications |

No unverified reference numbers were introduced into the final results.

## Independent derivation checks

`tools/check_task_2_4_reference.py` checks the algebra without importing the
simulation Hamiltonian builders:

- Direct Fourier averaging of the laboratory memory drive confirms the chosen
  creation-operator phase coefficient, with absolute error 1.96e-17.
- Period averaging of the laboratory first-pump-order polynomial through fifth
  phase order agrees with the displayed resonant Hamiltonian to 8.59e-13/us on
  a low-Fock block. This tests the exchange sign, cosine factor, both
  number-dependent coefficients and the normal-order correction.
- A direct overlap of two emitted coherent states verifies the coherence-decay
  exponent kappa_b|DeltaB|²/2, with absolute difference below 3e-14/us in the test.

The checks use a declared low-Fock projection to avoid truncated-commutator
edges and exact periodic quadrature for the finite polynomial. They verify
retained algebra and normalization, not the adequacy of the physical circuit
approximation. Results and source SHA256 are saved in
`reviews/task_2_4_reference_checks.json` and indexed with the final evidence.

## The single (c-d) storyline

1. At fixed cat size, a stronger memory force increases both contrast and
   estimated logical relaxation; raising the drive alone has an error cost.
2. Temporarily increase alpha from 2.1 to 2.6 using the buffer microwave, keep g2
   fixed and read with epsilon_Z/g2=.1. Use 2-us enlargement and return ramps,
   a 41.3997-us readout and 2-us final recovery.
3. Compare the complete 47.3997-us cycle with the specified 110.2205-us weak
   reference at the same information target I=1.
4. Explain the 1.616 field gain from 2(2.1/2.6), check the separate static rate,
   and directly measure recovered logical population and leakage.
5. Retain the scientific limit: the full cycle is demonstrated in the ideal
   cubic two-mode model. Corrected-circuit static tests do not validate that
   full cycle, and ideal mean-signal information does not establish single-shot
   fidelity.

The optional fast variant, fixed-size shape search, 78-fold plateau diagnostic,
optimizer settings and depletion-model failure are preserved in appendices.
They no longer compete with the main protocol or interrupt its motivation and
validation. No hybrid enlargement-plus-depletion claim is made.
