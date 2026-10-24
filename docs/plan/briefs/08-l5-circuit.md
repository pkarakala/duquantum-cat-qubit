# Brief `l5-circuit`: Task 2.4a: what survives from the ATS circuit Hamiltonian

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l5-circuit`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/08-l5-circuit.md`, then execute this brief exactly. Keep `docs/plan/status/l5-circuit.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l5-circuit` | `std/l5-circuit` (from `standard-track`) | `l0-core` | strongest reasoning model available (Opus class) | 3 h | Phase 1–2 (start after G0, 6:45 PM Sat Oct 24) / **11:30 PM Sat** |

## 1. Goal and why
Task 2.4a asks: how does the readout drive really enter the circuit Hamiltonian, and which terms besides g₂a²b† survive the expansion + RWA? Every other lane uses the effective model by hand. You derive it from the circuit, put numbers on what it leaves out (Stark shifts, Kerr, cross-Kerr, dressed g₂, readout-drive side terms), check it with a time-dependent circuit simulation, and hand `l4b-tradeoff` an `extra_H` recipe. Two headline findings to confirm or refute **numerically**: (i) g₂ = −½E_Jε_pφ_a²φ_b·e^{−Φ/2}, so the ½ is right (the iQuHACK tutorial drops it) and ε_p ≈ 0.037–0.038 is needed, not 0.035; (ii) the pump Stark-shifts the buffer by ≈ 2π·26 MHz ≫ g₂, κ_b, so **the pump and buffer-drive frequencies must be retuned**.

## 2. Read first
- `CONTRACT.md` §1 (your allowlist), §2 (env, quick vs production, heavy-job limits), §3 (`two_mode(..., extra_H=)`), §6 (records, IDs §6.3, `dirty`), §7 (`convergence_block`), §10 (your four functions), §14, §15.
- `RESEARCH.md` §1 (parameters), §2 (`dq.timecallable`, `dq.modulated`, `Tsit5` `max_steps`), §4.3 (Kerr/Stark from `extra_H` break the antiunitary symmetry), **§8 (all of it)**, §11 (Réglade, Ferrari).
- `docs/challenge_prompt_v4.md` Task 2.4 (the H_circuit, parameter table, tractability note, part a).
- Style: `src/config.py`, `src/model.py`, `src/results.py`, `tasks/task_1_3a.py` (short docstrings, `argparse` main, `from src import config as C` first, figures via `src.plotting.save`, numbers via `src.results`).

## 3. Allowlist (touch nothing else)
`src/circuit.py`, `tasks/task_2_4a.py`, `docs/derivation_2_4a.md`, `tests/test_l5_circuit.py`, `docs/plan/status/l5-circuit.md`; production outputs `results/records/t2_4a.*.json`, `results/arrays/t2_4a.*.npz`, `figures/task_2_4a_*.png`. No edits to `src/model.py`, `src/config.py`, `requirements.txt`, other lanes' files, `notes/`, `prep/`. Need something there → DECISION NEEDED.

## 4. Interfaces you implement / rely on
**Units:** all `src/circuit.py` inputs/outputs in rad/µs (multiply GHz/MHz by `C.TWO_PI` **once**, in the task script); records report value/2π in **MHz**. ω₀ = 2π·0.8 GHz = 2π·800 rad/µs; (ω_a, ω_b, ω_p) = (5, 6, 4)·ω₀; E_J = 2π·40 000; φ_a = 0.06, φ_b = 0.3; Φ = φ_a²+φ_b² = 0.0936, e^{−Φ/2} = 0.954278.
```python
# CONTRACT §10 — exact names; you fix the details below
def sin_phi_terms(phi_a, phi_b, max_order) -> list[dict]:
    """All (p,q,r,s), n=p+q+r+s odd <= max_order: {'p','q','r','s','order': n, 'coef': float}
    coef = e^{-Φ/2} i^{n-1} φa^{p+q} φb^{r+s} / (p! q! r! s!)  (real: i^{n-1} = ±1). Operator = a†^p a^q b†^r b^s."""
def term_frequency(term, w_a, w_b) -> float:          # (p-q) w_a + (r-s) w_b   (frame a -> a e^{-i w_a t})
def resonant_terms(terms, w_a, w_b, w_p, tol) -> list[dict]:
    """Terms with |term_frequency - s*w_p| <= tol for s = +1 or -1; each dict gains 'freq' and 'sideband': s."""
def g2_from_circuit(EJ, eps_p, phi_a, phi_b) -> float:   # -(1/2) EJ eps_p phi_a^2 phi_b e^{-Φ/2}, units of EJ

# lane-internal helpers (yours; may change without a DECISION)
def shifted_coef(p, q, r, s, phi_a, phi_b, shift):       # coefficient in sin(φ̂ + shift), see §6 step 4
def xi_steady(EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p, w0, n_t=512, n_iter=50, tol=1e-12) -> dict  # {'t','xi_a','xi_b','phi_cl','iters'}
def static_terms(EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p, w0, max_order=7, displaced=True, tone=None, n_t=512) -> list[dict]
    # tone=(eps_r, w_r, phase): first-order-in-eps_r terms of an extra flux tone instead of the pump terms
def eps_p_for_g2(target, EJ, phi_a, phi_b, w_a, w_b, w_p, w0, displaced=True) -> float   # brentq on [0.03, 0.045]
def circuit_rotating_H(Na, Nb, EJ, eps_p, phi_a, phi_b, w_a, w_b, w_p_pump, max_order=5, coef_floor=2*pi*1e-4)  # dq.timecallable
def extra_H(Na, Nb, kerr_a, kerr_b, chi_ab, delta_a=0.0, delta_b=0.0)    # QArray on (Na, Nb)
```
You rely on: `src.config` (`TWO_PI, G2, KAPPA_B, KAPPA_A, METHOD, METHOD_LONG`), `src.model.two_mode` (with `extra_H`), `vacuum2`, `src.results.record / save_arrays / std_params / load_record`, `src.convergence.convergence_block`, `src.plotting.save(fig, name, quick=)`.

## 5. Tests to write FIRST (TDD)
`tests/test_l5_circuit.py`, all fast (`not slow`) unless marked; write them, see them fail, commit, then implement.
1. `test_normal_order_coefficient_vs_bruteforce`: Fock N = 30 per mode, φ_a = 0.06, φ_b = 0.3; φ̂ = φ_a(A+A†)+φ_b(B+B†) as a 900×900 real symmetric matrix; S = V sin(Λ) Vᵀ via `numpy.linalg.eigh`. Assert `|<0_a,1_b|S|2_a,0_b> − √2·c(0,2,1,0)| < 1e-8` (a²|2⟩ = √2|0⟩; only a²b† contributes, c(0,2,1,0) = −e^{−Φ/2}φ_a²φ_b/2). Also, for every m+n odd ≤ 7: `|<0,0|S|m,n> − √(m!n!)·c(0,m,0,n)| < 1e-8`. (A scratch check gave a difference of 7e-16.)
2. `test_displaced_closed_form_vs_bruteforce`: for a constant shift φ_c = 0.2, S_c = sin(φ̂ + φ_c) by eigendecomposition; for all m+n ≤ 6, `<0,0|S_c|m,n> == √(m!n!)·shifted_coef(0,m,0,n, φa, φb, 0.2)` to 1e-8 (even n included).
3. `test_resonant_family_order7`: `terms = sin_phi_terms(0.06, 0.3, 7)`; `res = resonant_terms(terms, 5*w0, 6*w0, 4*w0, tol=1e-6*w0)`. Assert `len(res) == 12`, every term has (p−q, r−s) ∈ {(−2, 1), (2, −1)}, the set contains (0,2,1,0), (2,0,0,1), (1,3,1,0), (0,2,2,1); and the minimum |freq ∓ ω_p| over the non-resonant terms equals ω₀ (rel 1e-12).
4. `test_g2_value`: `g2_from_circuit(TWO_PI*4e4, 0.035, 0.06, 0.3)/TWO_PI == -0.72143` (rel 1e-4); ε_p for 0.763 MHz, `0.035*0.763/0.72143`, within 5e-5 of 0.03702; and it equals 2E_Jε_p·½·c(0,2,1,0) from `sin_phi_terms` (rel 1e-12).
5. `test_sign_convention`: (a) on 100 random scalars x, φ: `-2EJ*cos(-pi/2+x)*cos(phi+pi/2) == 2EJ*sin(x)*sin(phi)` (abs 1e-9); (b) g2 < 0; (c) with a pump phase θ = π, the static a²b† coefficient flips sign (rel 1e-12); (d) `two_mode(12, 4, g2=-C.G2, eps_d=C.G2, ...)` from vacuum for 1 µs gives Re⟨a²⟩ < 0, and with +C.G2 Re⟨a²⟩ > 0 (cat on the imaginary vs real axis).
6. `test_displaced_frame_static`: at ε_p = 0.035, `xi_steady` converges in < 50 iterations; linear-response peak |ξ_a| = 0.1113, |ξ_b| = 0.3006 (rel 1e-3, first iteration), self-consistent 0.1098 / 0.2967 (rel 1e-2); the static linear coefficients of a, b are < 1e-9 MHz; exact ratios kerr_b/stark_b = −φ_b²/4, chi_ab/stark_b = −φ_a², kerr_a/stark_a = −φ_a²/4 (rel 1e-9); n_t = 256 vs 1024 agree to 1e-10.
7. `test_readout_tone_terms`: a flux tone at ω_a, undisplaced: the ratio of a†a² to a coefficients = −φ_a²/2 and of ab†b to a = −φ_b² (rel 1e-9); displaced: the beam-splitter ab† coefficient / linear-a coefficient ∈ [0.025, 0.032].

## 6. Method, step by step
1. **Setup.** Create the worktree branch `std/l5-circuit` from `standard-track`; copy `docs/plan/status/_TEMPLATE.md` to `status/l5-circuit.md` ("started"). Write the §5 tests, commit, status "tests written".
2. **Sign algebra.** With φ_Δ = π/2 and φ_Σ = −π/2 + x: cos φ_Σ = sin x and cos(φ̂+π/2) = −sin φ̂, so −2E_J cos φ_Σ cos(φ̂+φ_Δ) = **+2E_J sin(ε_p cos ω_pt)·sin φ̂** ≈ 2E_Jε_p cos(ω_pt) sin φ̂. There is no static ATS term at this bias. Note sin(ε_p cos θ) = 2Σ(−1)^k J_{2k+1}(ε_p)cos((2k+1)θ): the fundamental is 2J₁(ε_p) ≈ ε_p(1 − ε_p²/8), a 1.5e-4 relative correction, and 3ω_p = 2ω_b is harmless because only even operators could use it and sin φ̂ is odd (no b†²).
3. **Normal ordering (BCH).** e^{A+B} = e^A e^B e^{−[A,B]/2} with A = iφ_a a†, B = iφ_a a, [A,B] = φ_a², so e^{iφ̂} = e^{−Φ/2}e^{iφ_a a†}e^{iφ_a a}e^{iφ_b b†}e^{iφ_b b}. Hence sin φ̂ = Σ_{odd n} c_pqrs a†^p a^q b†^r b^s with the CONTRACT coefficient. Implement the four contract functions. **Resonance rule:** a†^p a^q b†^r b^s rotates at (5Δa + 6Δb)ω₀ with Δa = p−q, Δb = r−s; with the fundamental pump it is static iff 5Δa + 6Δb = ±4. Through order 7, only the a²b† family is static: 6 monomials (a²b†, a†a³b†, a²b†²b, a†²a⁴b†, a†a³b†²b, a²b†³b²) plus h.c. = 12. g₂ = 2E_Jε_p·½·c(0,2,1,0) = **−½E_Jε_pφ_a²φ_b e^{−Φ/2}** (combinatorics 2·½·3·⅙ = ½); |g₂|/2π = 0.5·40000·0.035·0.0036·0.3·0.9543 = **0.7214 MHz** at ε_p = 0.035, and **ε_p = 0.03702** for 0.763 MHz. Sign: g₂ < 0, so with −ε_d(b+b†) we get α² = ε_d/g₂ < 0 (cat on the imaginary axis); a pump phase π (g₂ → +|g₂|) or flipping ε_d restores it, a gauge choice. Also list the higher-pump-harmonic "formal" resonances (from J₃, J₅, … and the displacement): a²b³ (order 5, at 7ω_p), a²b†⁵ (order 7, 5ω_p), a†⁴b² (order 6, 2ω_p, about 4e-6 MHz). Give each its coefficient and call it negligible.
4. **Displaced frame BEFORE the RWA (the core).** The order-1 pump term 2E_Jε_p cos(ω_pt)·e^{−Φ/2}[φ_a(a+a†)+φ_b(b+b†)] is a strong off-resonant drive: 2π·84 MHz on the memory at 0.8 GHz detuning, 2π·420 MHz on the buffer at 1.6 GHz. Solve iξ̇ = ωξ + F(t) exactly in Fourier space on a grid of n_t points over the common period T₀ = 2π/ω₀ = 1.25 ns: ξ(t) = Σ_k X_k e^{ikω₀t}, X_k = −F_k/(ω + kω₀). Keep counter-rotating parts; mask k = −5 and −6, where F_k = 0. Self-consistent force: F_a(t) = 2E_J sin(ε_p cos ω_pt)·e^{−Φ/2}φ_a·cos φ_cl(t), with φ_cl = 2φ_a Re ξ_a + 2φ_b Re ξ_b; iterate to max|Δξ| < 1e-12, starting from cos φ_cl = 1 (the linear response: ξ_a = A e^{−iω_pt} + B e^{iω_pt}, A = −F/(ω_a−ω_p), B = −F/(ω_a+ω_p)). Neglect κ in ξ (κ_b/2Δ ~ 1e-3; say so). **Exact closed form:** since a → a+ξ is the same as φ̂ → φ̂ + φ_cl and e^{i(φ̂+c)} = e^{ic}e^{iφ̂}, the displaced ATS term is 2E_J sin(ε_p cos ω_pt)·Σ_{all n} e^{−Φ/2} **sin(φ_cl(t) + nπ/2)** φ_a^{p+q}φ_b^{r+s}/(p!q!r!s!) a†^p a^q b†^r b^s. With a self-consistent ξ, all n = 1 terms cancel against the frame term. Static coefficient = mean over the grid of [that time function × e^{i(5Δa+6Δb)ω₀t}]. Use n_t = 512; it is exact for harmonics below 256 ω₀. Number-conserving monomials then share **one** number C₂ = 2E_J⟨sin(ε_p cos ω_pt) sin φ_cl⟩: stark_a = −C₂e^{−Φ/2}φ_a², stark_b = −C₂e^{−Φ/2}φ_b², kerr_a = C₂e^{−Φ/2}φ_a⁴/4, kerr_b = C₂e^{−Φ/2}φ_b⁴/4, chi_ab = C₂e^{−Φ/2}φ_a²φ_b² (convention: **H ⊃ kerr·a†²a², chi·a†a b†b**; in the −(K/2)a†²a² convention K = −2·kerr). Analytic cross-check: C₂ ≈ −2E_J²ε_p²e^{−Φ/2}Σ_i 2φ_i²ω_i/(ω_i²−ω_p²) ≈ −2π·271 MHz at ε_p = 0.035.
   **Scratch numbers (numpy, reproduce, don't trust):** at ε_p = 0.035, g₂,disp = −0.7115, stark_a = +0.915, stark_b = +22.86, kerr_a = −8.2e-4, kerr_b = −0.514, chi_ab = −0.0823 MHz. Find **ε_p\*** with |g₂,disp| = 0.763 MHz (`eps_p_for_g2`): ≈ **0.03761**, giving stark_a ≈ 1.053, stark_b ≈ 26.33, kerr_a ≈ −9.5e-4, kerr_b ≈ −0.592, chi_ab ≈ −0.0948 MHz. **Retuning:** pump ω_p' = ω_p + 2·stark_a − stark_b (+2·kerr_a for |2,0⟩) ≈ 3.2 GHz − 24.2 MHz; buffer drive at ω_b + stark_b (26 MHz ≫ κ_b/2π = 2.6 MHz, so without retuning there is no cat). Also tabulate the dressed-g₂ family coefficients and g₂(n_a = α² = 4.41) relative to g₂.
5. **How the readout drive enters** (and the buffer drive), first order in the tone, via `static_terms(tone=...)`:
   - (a) Capacitive drive 2ε_Z cos(ω_r t)(a+a†) with ω_r = ω_a + stark_a (must follow the Stark shift; ≈1 MHz is not small next to g₂). It gives ε_Z(a+a†) plus counter-rotating terms at 2ω_a; the Bloch–Siegert shift ε_Z²/2ω_a ≈ 7e-5 MHz at ε_Z = g₂ is negligible.
   - (b) Extra ATS flux tone ε_r cos(ω_r t) on φ_Σ. It gives ε_Z = E_Jε_rφ_a e^{−Φ/2} (ε_r ≈ 3.3e-4 rad for ε_Z = g₂), plus dressed terms −(φ_a²/2)ε_Z·a†a² (n̂a) and −φ_b²ε_Z·ab†b, plus, through the pump displacement, a **resonant beam splitter** g_bs(ab† + a†b) with g_bs ≈ 0.0285ε_Z. It is exactly resonant because ω_a − ω_p = ω_b − ω_a, even after the shifts. Estimate its extra memory loss 4g_bs²/κ_b (≈ 0.04/µs at ε_Z = 3g₂, comparable to κ_a = 0.058/µs) and flag it for 2.4b/2.4c.
   - (c) If ε_d is applied as a flux tone at ω_b: g_sp(b†²b + b†b²) with g_sp = −(φ_b²/2)ε_d ≈ −0.045ε_d (Réglade's g_sp), plus a tiny memory two-photon drive ≈ 5.7e-4·ε_d(a² + h.c.).
   - Map onto the parasitics. Réglade's g_lin(b+b†) is our order-1 pump term: off-resonant here, so it shows up as ξ_b and the Stark shifts (with a resonant linear tone they cancel it with an opposite tone). Réglade's g_sp and spurious Kerr are covered above. Ferrari's cross-Kerr χ drives bit-flip saturation; their realistic values are K_b/2π = 1 MHz, χ/2π = 0.5 MHz, against ours of K ≈ 1.18 MHz and χ ≈ 0.095 MHz.
6. *(Stretch, cut first.)* **Second-order RWA (van Vleck).** H⁽²⁾ = Σ_{k≥1}[H_k, H_{−k}]/(kω₀) for H(t) = Σ_k H_k e^{ikω₀t} (the displaced, rotating-frame H, order ≤ 5). Build the matrices on (Na+4, Nb+6) and read the shifts from low Fock elements (for example ⟨1,0|H⁽²⁾|1,0⟩ − ⟨0,0|H⁽²⁾|0,0⟩). Compare with step 4 and with the V1 δ_fit.
7. **Validation simulation (`circuit_rotating_H`).** Bare rotating frame at ω_a, ω_b; normal-ordered monomials of order ≤ 5 including the order-1 drive (do **not** pre-displace: this independently tests step 4); drop |2E_Jε_p·c| < 2π·100 Hz. H(t) = 2E_J sin(ε_p cos ω_p't)·Σ_g e^{iν_g t}O_g (+ drive), built as `dq.timecallable(lambda t: dq.asqarray(P(t)*jnp.einsum('k,kij->ij', jnp.exp(1j*nu*t), O_stack)))` with O_stack precomputed. Solver: `dq.method.Tsit5(rtol=1e-8, atol=1e-10, max_steps=10_000_000)`. The fastest terms are about 8 GHz, so steps must be ≲ 10 ps: check that rtol 1e-10 changes observables by < 1e-4. Initial state is the **displaced** vacuum/Fock state D(ξ_a(0))D(ξ_b(0))|·⟩ (linear-response ξ at ω_p'); measure in the displaced frame (⟨n_a⟩_d = ⟨a†a⟩ − 2Re(ξ_a*⟨a⟩) + |ξ_a|², with ξ_rot = ξ_lab e^{iω_a t}). Fallback: a sin² pump ramp of 10 ns. All at ε_p\*.
   - **V1 (fits g₂, settles the ½).** |2_a,0_b⟩ → |0_a,1_b⟩ exchange, no drive, no loss, `dq.sesolve`, 0.3 µs, Na = 10, Nb = 8 (convergence: Na 8/10, Nb 6/8). Fit P₀₁(t) = [4G²/(4G²+δ²)] sin²(√(4G²+δ²)·t/2), with G = √2|g₂| and free δ. Prediction: G = 2π·1.079 MHz, full transfer at 0.232 µs. Run (a) the bare pump ω_p (expect max P₀₁ ≈ 4G²/(4G²+δ²) ≈ 0.008 with δ = 2π·24 MHz) and (b) the retuned ω_p'. If max P₀₁ < 0.95, retune once by δ_fit and report δ_fit as the second-order shift. The no-½ (iQuHACK, g₂ = E_Jε_pφ_a²φ_b ≈ 1.63 MHz at ε_p\*) prediction is plotted for contrast.
   - **V2 (inflation, 150–200 ns).** From the displaced vacuum with retuned pump, buffer drive −ε_d(b e^{i·stark_b·t} + h.c.), jumps √κ_b b and √κ_a a, 0.2 µs, 401 saves, `save_states=False`. **Use α_v² = 1 (ε_d = C.G2), Na = 12, Nb = 6 (check Nb = 8).** At α = 2.1, ⟨n_b⟩ reaches ≈ 4 within 200 ns, so Nb ≈ 5 is not converged; that run (Nb = 12) goes to "Jobs to queue". Compare ⟨n_a⟩(t) and ⟨b⟩_eff = ⟨b_d⟩e^{i·stark_b·t} with `two_mode` (same frame, g₂ = g₂,disp < 0): (E0) no extra_H; (E1) `extra_H(kerr_a, kerr_b, chi_ab)`; (E2) the no-½ g₂. Report max|Δn_a| and max|Δ⟨b⟩| for each, and check Re⟨a²⟩ < 0 in the tdsim (the sign claim).
8. **Write `docs/derivation_2_4a.md`.** Harshit presents from it, so keep it plain and in order: H_circuit and the sign; BCH; frame and resonance rule (units of 0.8 GHz); g₂ with ½ and e^{−Φ/2}; displaced frame and the C₂ formulas; the retuning; the readout drive (a/b/c); parasitics mapping; validation (figure); what is neglected. Include a **term table** with columns term | order | frequency (×0.8 GHz, and GHz) | coefficient (MHz) | resonant? covering at least the a²b† family, a, b, a†a, b†b, a†²a², b†²b², a†ab†b, ab†, a†a², b†b², ab†b and the tone terms. Tag numbers `rec:<id>=<value>` (CONTRACT §11) so `l7-docs` can copy them. Put the `extra_H` recipe (§12) in the doc as well.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
`tasks/task_2_4a.py --part {sym,tdsim,all} [--quick]`. Every record uses `params = std_params(EJ_GHz=40, phi_a=0.06, phi_b=0.3, wa_GHz=4.0, wb_GHz=4.8, wp_GHz=3.2, eps_p=..., max_order=...)`.

| ID (exact) | value (units) | method string | convergence | cross_check (tol) |
|---|---|---|---|---|
| `t2_4a.g2.sym.circuit` | g₂/2π signed, ε_p = 0.035, undisplaced: −0.7214 (MHz) | `normal_ordered_bch_rwa1` | null + notes (closed form) | brute-force matrix element (1e-6); `t2_4a.g2.tdsim.circuit` rescaled to 0.035 (0.03) |
| `t2_4a.stark_a.sym.circuit` | stark_a/2π at ε_p\* (MHz) | `displaced_frame_rwa1` | axis `n_t` [256, 512, 1024], rel_tol 1e-8 | analytic C₂ estimate (0.05) |
| `t2_4a.stark_b.sym.circuit` | stark_b/2π at ε_p\* (MHz) | same | same | analytic C₂ (0.05); V1-calibrated 2s_a − s_b (0.1) |
| `t2_4a.kerr_a.sym.circuit`, `t2_4a.kerr_b.sym.circuit`, `t2_4a.chi_ab.sym.circuit` | raw coefficients (MHz), H ⊃ value·op | same | same | analytic C₂ (0.05) |
| `t2_4a.resonant_terms.sym.circuit` | 12 (count), max_order 7; list in `notes` | `rwa_frequency_scan` | null + notes | independent integer scan of 5Δa+6Δb = ±4 (0) |
| `t2_4a.g2.tdsim.circuit` | fitted \|g₂\|/2π at ε_p\* (MHz) | `tdsim_rabi_fit` | Na, Nb sweep (rel_tol 2e-3) | g₂,disp (0.03); g₂.sym rescaled (0.03) |

Put ε_p\*, g₂,disp, the dressed family, δ_fit, the V2 errors and the tone ratios into `notes` of the closest record. Arrays: `results/arrays/t2_4a.resonant_terms.sym.circuit.npz` (term table) and `results/arrays/t2_4a.g2.tdsim.circuit.npz` (t, P₀₁ for each run, V2 traces). Figures: `figures/task_2_4a_validation.png` (V1 P₀₁: bare vs retuned vs ½/no-½ predictions; V2 ⟨n_a⟩ and ⟨b⟩: tdsim vs E0/E1/E2), plus optionally `figures/task_2_4a_terms.png` (|coef| per term, log scale, resonant ones highlighted).
**Quick** (≤ 2 min → `results/quick/`, `figures/quick/`): max_order 5, n_t 256, V1 0.1 µs at Na = 6, Nb = 4, V2 40 ns at Na = 8, Nb = 4. **Production:** sym takes seconds; V1 a few minutes; V2 at α_v² = 1 is expected ≤ 15 min (lane runs and commits it; if > 15 min, queue it). **Jobs to queue:** V2 at α = 2.1, Na = 16, Nb = 12 (`--alpha2 4.41 --nb 12`, ~2 GB).

## 8. Acceptance gates (ALL must pass before DONE)
1. All §5 tests pass; `& $env:DUQ_PY -m pytest -m "not slow" -q` stays under 2 min overall.
2. g₂.sym = −0.7214 MHz (4 s.f.); ε_p for 0.763 = 0.0370; ε_p\* reported; the sign/gauge statement is in the doc.
3. Resonant count = 12 through order 7, with the list in notes and the doc.
4. Displaced static linear terms < 1e-9 MHz; the five ratios hold; stark_b at ε_p\* in [20, 32] MHz (else DECISION NEEDED: a ×2 or sign error is likely).
5. V1: tdsim |g₂| within 3% of |g₂,disp|, and the no-½ value (×2.13) excluded by > 20σ of the fit; bare-pump max P₀₁ < 0.05; retuned (≤ 1 recalibration) ≥ 0.95; rtol-tightening change < 1e-4; Na/Nb converged.
6. V2: E1 max|Δn_a| ≤ 0.03, and E2's error ≥ 5× E1's; Re⟨a²⟩_tdsim < 0.
7. Every production record has `provenance.dirty == false`, a non-empty `cross_check` with `agree: true`, and convergence per the table.
8. `docs/derivation_2_4a.md` complete with the term table and the `extra_H` recipe; status file at DONE (§12).

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY -m pytest tests/test_l5_circuit.py -q            # red first, then green
& $env:DUQ_PY -m pytest -m "not slow" -q
& $env:DUQ_PY -m tasks.task_2_4a --quick                       # smoke, <= 2 min
git status --porcelain -- src tasks tools                       # must be empty: commit code first
& $env:DUQ_PY -m tasks.task_2_4a --part sym
& $env:DUQ_PY -m tasks.task_2_4a --part tdsim                   # then commit records/arrays/figures
# for the integrator (put in the status file, do not run the worker yourself):
# python -m tools.runq submit --name l5_v2_a2.1 --ram-gb 2 -- $env:DUQ_PY -m tasks.task_2_4a --part tdsim --alpha2 4.41 --na 16 --nb 12
```

## 10. Out of scope / do not
- Do not run 2.4b sweeps or Γ_X with `extra_H` (that is `l4b-tradeoff`). No pulse design (that is `l4c-capstone`).
- No full-GHz lab-frame simulation over µs, and no tdsim longer than 0.3 µs in-lane.
- Do not edit `src/model.py`, `src/config.py`, `requirements.txt` or CONTRACT; do not change the four §10 signatures.
- Do not treat RESEARCH §8 or this brief's scratch numbers as results: reproduce them. Do not report a number without a record.
- No sympy dependency is required (the closed forms are exact and numeric); if you use sympy for the doc, keep it out of the tests' hot path.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write in the status file:
```
DECISION NEEDED (l5-circuit): <one line>
Evidence: <numbers, record ids, figure>
Options: A) ... B) ...   My recommendation: ...   Blocking: yes/no
```
Triggers: V1 |g₂| differs from ½-formula by > 3% but is not ×2; stark_b outside [20, 32] MHz; `convergence_block` rejects a non-Na/Nb axis such as `n_t` (fallback: `convergence: null` + the n_t sweep in notes); V2 > 15 min; E0 beats E1 beyond noise (check the extra_H sign).
Fallbacks: pump ramp instead of a displaced initial state; Nb = 8 for V2 if Nb = 6 is not converged; drop order-5 terms below 2π·1 kHz if V2 is slow.
**Cut line:** if the displaced-frame part (step 4) stalls after 2 h, ship the static term table, order-of-magnitude shifts from the analytic C₂ formula (labelled "estimate"), and V1/V2 **without** second-order terms (E0 only), and say so in the doc and the status file. Step 6 is always cut first.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
`docs/plan/status/l5-circuit.md` at DONE must contain: branch and last commit; tests passed/total; a table of every record ID with its value and units; ε_p\*, ω_p' and the buffer-drive frequency; V1 (G, δ_fit, max P₀₁ bare/retuned) and V2 (E0/E1/E2 errors); the tone ratios (g_bs/ε_Z, g_sp/ε_d); anything cut; open DECISIONs; "Jobs to queue" (V2 at α = 2.1); and this **extra_H recipe for `l4b-tradeoff`**:
```python
import dynamiqs as dq
from src import config as C
from src.model import two_mode
from src.results import load_record

def circuit_extra_H(Na, Nb):
    """eps_p^2 terms of the ATS (frame of the Stark-shifted modes; pump and buffer drive retuned)."""
    v = lambda q: C.TWO_PI * load_record(f"t2_4a.{q}.sym.circuit")["value"]      # MHz -> rad/us
    a, b = dq.destroy(Na, Nb)
    return (v("kerr_a") * a.dag() @ a.dag() @ a @ a + v("kerr_b") * b.dag() @ b.dag() @ b @ b
            + v("chi_ab") * a.dag() @ a @ b.dag() @ b)

H, jumps, (a, b) = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=eps_z, extra_H=circuit_extra_H(Na, Nb))
# Valid with C.G2 > 0 (pump phase pi): Kerr/chi are invariant under the pump phase. Stark terms are omitted
# because the pump and drive are retuned; for an un-retuned what-if add v("stark_a")*a.dag()@a + v("stark_b")*b.dag()@b.
# Flux-tone readout option: add g_bs*(a@b.dag() + a.dag()@b) with g_bs = (ratio in notes) * eps_z.
```
**Judge questions for Harshit (questions only):**
1. Your g₂ has an extra e^{−(φ_a²+φ_b²)/2} and a ½ that a public tutorial leaves out. Where does each factor come from, and how did your simulation decide between them?
2. The pump shifts the buffer by about 26 MHz, roughly 35 times g₂. Why does that not destroy the cat, what exactly has to be retuned, and what would you see in the lab if it were not?
3. If the readout drive is applied through the ATS flux instead of capacitively, which new terms appear, why is one of them exactly resonant, and how would it change Γ_X or Γ_Z?
