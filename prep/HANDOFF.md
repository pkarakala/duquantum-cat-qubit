# DuQuantum 2026 · Alice & Bob Cat-Qubit Challenge · Handoff

> **For a new Claude chat:** this file is the full context from the prep conversation. Read it before helping. Pranav is an ECE undergrad (UCSB) with a background in photonics, quantum computing and compiler/systems work, competing in the Alice & Bob challenge. The real challenge prompt has **not** been seen yet; everything under "Likely tasks" is inference from the tutorial notebooks.

---

## 1. Status

| Item | State |
|---|---|
| Local project | `~/projects/duquantum-cat-qubit` (venv in `.venv`, run `source .venv/bin/activate`) |
| GitHub | `github.com/pkarakala/duquantum-cat-qubit`, private, branch `main` |
| Environment check | `python check_env.py` should print `final <n> ≈ 4` |
| Prep material | `prep/` (this file, guide PDF, interactive lab, Hacker Guide) |
| Tutorials | `notebooks/tutorials/` (the three notebooks from Discord) |
| Challenge prompt | **Not yet released.** Paste it into the chat as soon as hacking starts. |

**Before making the repo public for Devpost:** remove or ignore `prep/DuQuantum_2026_Hacker_Guide.pdf` (it contains organizer phone numbers). It is already in `.gitignore`.

---

## 2. Event logistics (from the official Hacker Guide, Oct 20)

- **Hacking:** Sat Oct 24, 11:30 AM → Sun Oct 25, 11:30 AM. In person only. Wilkinson Building, 534 Research Dr, Durham.
- **Check-in:** Sat 9:00–11:00, Wilkinson 0th-floor lobby. Bring HackDuke QR code, government ID, university ID.
- **Opening + keynote:** Sat 10:30–11:30, Wilkinson 021.
- **Alice & Bob judging:** **Sun 12:00–1:30, Wilkinson 132.**
- **Closing / awards:** Sun 3:30–4:30, Wilkinson 021.
- **Announcements:** Discord only (not email). Questions: #questions, or DM Derek (@wxr262).
- **Hacking rooms:** 021, 126, 132, 136, Learning Commons, 1st-floor lobby, 181. Not 130.
- **Meals:** Sat lunch 11:30, Sat dinner 6:30, Sun brunch 10:00.

### Deliverables (due Sun 11:30 AM)
1. Live presentation/demo, **≤ 8 min** (weighted most)
2. Full repo on **Devpost** (weighted most)
3. Video demo, **≤ 4 min**, on Devpost

### What judges want
- Understanding of the problem and its theory
- **Your own reasoning, not an LLM's.** Be able to explain every line.
- Reproducible numerics
- What you learned and what went wrong
- Every rubric item in the sponsor prompt

Understanding and growth count as much as the result. Tracks: Introductory and Standard (confirm which).

### 24-hour plan
| Time | Goal |
|---|---|
| 11:30–1:00 | Read prompt twice, copy rubric into README, ask mentors, verify env on every laptop |
| 1:00–6:00 | Easiest scored part, end to end |
| 6:00–2:00 | Harder parts, sweeps, plots; commit often |
| 2:00–7:00 | Sleep |
| 7:00–10:00 | Final results, README, slides |
| 10:00–11:30 | Record video, submit, rehearse talk |

---

## 3. The physics

**Idea.** Store a qubit in an oscillator as two far-apart coherent states, |0⟩ ≈ |+α⟩ and |1⟩ ≈ |−α⟩. A bit flip needs a jump across phase space, so it is exponentially suppressed. A phase flip is a single lost photon, so it grows only linearly with cat size. Only phase flips then need correcting (repetition code instead of surface code).

### Key formulas

- Coherent state: a|α⟩ = α|α⟩, mean photons n̄ = |α|², overlap ⟨α|−α⟩ = e^{−2|α|²}
- Cats: |C±⟩ = (|α⟩ ± |−α⟩) / √(2(1 ± e^{−2|α|²})); even/odd photon numbers only
- Cat-basis dictionary: X ≈ parity P = e^{iπa†a}; Z ≈ |α⟩⟨α| − |−α⟩⟨−α|; a|C+⟩ ∝ |C−⟩ (photon loss = phase flip)
- Lindblad: ρ̇ = −i[H,ρ] + Σ (LρL† − ½{L†L, ρ}); jump operators carry √rate
- Two-photon dissipation: **L₂ = √κ₂ (a² − α²)**; L₂|±α⟩ = 0; parity conserved (vacuum → |C+⟩, |1⟩ → |C−⟩)
- Mean field: **ȧ = −κ₂ a\*(a² − α²) − (κ₁/2) a**. Fixed points only at a = ±α (wells shrink to a² = α² − κ₁/(2κ₂)). Confinement rate **κ_conf = 2κ₂|α|²**.
- Error rates: **Γ_phase ≈ κ₁|α|²**, **Γ_bit ∝ e^{−2|α|²}** (scaling only; saturates with other noise); bias η = Γ_phase/Γ_bit

### Buffer elimination (be able to derive this on paper)

H = g₂ a†² b + g₂\* a² b† + ε_d\* b + ε_d b†, buffer loss √κ_b b.

1. ḃ = −i(g₂\* a² + ε_d) − (κ_b/2) b
2. Fast buffer (κ_b ≫ |g₂|, |ε_d|), set ḃ ≈ 0: b ≈ −(2i/κ_b)(g₂\* a² + ε_d)
3. ȧ = −i[a,H] = −2i g₂ a† b (using [a, a†²] = 2a†)
4. Substitute: ȧ = −(4|g₂|²/κ_b) a† (a² + ε_d/g₂\*)
5. Match to ȧ = −κ₂ a†(a² − α²):

**κ₂ = 4|g₂|²/κ_b,  α² = −ε_d/g₂\***

Validity: κ_b ≳ 10× g₂ and |ε_d|, ideally ≫ g₂|α|. Check numerically by comparing the two-mode and one-mode models.

### Gates (only if the prompt asks)
- Z rotation: H = ε_Z(a + a†) ≈ 2αε_Z Z
- X flip: e^{iπa†a}|α⟩ = |−α⟩
- Kerr cat: H = −K(a†² − α²)(a² − α²), α² = ε₂/K

### Notebook errata
- Phase flip written as |+⟩ ↔ |+⟩; should be |+⟩ ↔ |−⟩
- Logical |1⟩ formula repeats |−⟩; should be (|C+⟩ − |C−⟩)/√2
- Cat normalization N± missing a 1/√2 (code uses `dq.unit`, so numerics are fine)
- Dephasing rate mislabeled "single photon loss rate"

---

## 4. dynamiqs cheat sheet

```python
import dynamiqs as dq, jax, jax.numpy as jnp
n = 20
a = dq.destroy(n); N = a.dag() @ a
psi0 = dq.coherent(n, 2.0)                  # or dq.fock(n, 0)
cat = dq.unit(dq.coherent(n, 2.0) + dq.coherent(n, -2.0))
t = jnp.linspace(0, 10, 200)

r = dq.sesolve(H, psi0, t)                                   # closed
r = dq.mesolve(H, [jnp.sqrt(k1) * a], psi0, t, exp_ops=[N])  # open
r.states; r.expects[0]
dq.plot.wigner(cat); dq.plot.fock(cat); dq.plot.wigner_gif(r.states)

# one-mode two-photon loss
L2 = jnp.sqrt(k2) * (a @ a - alpha**2 * dq.eye(n))
r = dq.mesolve(dq.zeros(n), [L2], dq.fock(n, 0), t)

# memory + buffer (untested sketch; check docs)
na, nb = 20, 6
a = dq.tensor(dq.destroy(na), dq.eye(nb)); b = dq.tensor(dq.eye(na), dq.destroy(nb))
H = g2*a.dag()@a.dag()@b + g2*a@a@b.dag() + eps_d*b.dag() + eps_d*b
r = dq.mesolve(H, [jnp.sqrt(kb)*b], dq.tensor(dq.fock(na,0), dq.fock(nb,0)), t)
rho_a = dq.ptrace(r.states, 0, (na, nb))

# batching: add leading axes, e.g. jnp.sqrt(k1s)[:, None, None] * a
# gradients: wrap a sim in f(params) -> scalar, build operators inside, use jax.grad(f)
```

**Numerics:** Fock cutoff above |α|² + 5|α| then test convergence; buffer needs 3–6 levels; large κ_b is stiff/slow; in sweeps save `exp_ops`, not states; `dq.set_precision('double')` if noisy. Lifetimes: fit ⟨Z⟩(t) or ⟨P⟩(t), or use the slowest nonzero Lindbladian eigenvalue.

---

## 5. Likely tasks (inference, not the real prompt)

The cat notebook promises "basic circuit QED, the Hamiltonian of our system, how to obtain an approximate Hamiltonian" but never covers them, and ends: *"You will explore how you can engineer such an effective Hamiltonian in practice using superconducting circuit QED and simulate it using dynamiqs in the challenge."*

1. Warm-up: one-mode two-photon loss, cat formation, parity, n̄ ≈ |α|², fidelity
2. Derive the effective model from a pumped memory–buffer circuit (rotating-wave approximation → g₂a†²b + h.c., then buffer elimination)
3. Simulate two-mode vs one-mode; show agreement and breakdown
4. Add κ₁, κ_φ (maybe thermal); bit- and phase-flip times vs |α|² (headline plot)
5. Open-ended optimization

### Project ideas for the open-ended part
1. **Gradient-optimized cat preparation:** time-dependent ε_d(t), maximize fidelity with `jax.grad`
2. **Map of where buffer elimination fails:** batched sweep over κ_b/g₂ and α, heat map of model mismatch
3. **Bit-flip times beyond direct simulation:** Lindbladian spectrum at large α, with thermal-noise saturation
4. **Z-gate speed trade-off:** fidelity vs gate time, find the optimum
5. **Stretch:** feed simulated rates into a repetition-code logical-error estimate

Strategy: required parts first, then one idea pushed deep.

---

## 6. Files in `prep/`

- `HANDOFF.md`: this file
- `DuQuantum_Cat_Qubit_Guide.pdf`: phone-sized LaTeX guide (logistics, math, cheat sheet, self-test)
- `cat_qubit_lab.html`: offline interactive lab (Wigner explorer, phase-space flow, error bias, buffer calculator, derivation drill, self-test). Double-click to open.
- `DuQuantum_2026_Hacker_Guide.pdf`: official organizer guide (git-ignored)
