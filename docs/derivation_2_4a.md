# Task 2.4a: what the ATS circuit keeps, and what the pump shifts

Plain derivation for the readout write-up. Every tagged number is the value
`tasks/task_2_4a.py` writes into `results/records/`. Units: time in µs, rates in
rad/µs, and every MHz below is a rate divided by 2π. The fitted exchange
`t2_4a.g2.tdsim.circuit` is produced by the same script once `l0-core` is merged;
it is not quoted here.

## 1. The circuit Hamiltonian, and the sign

The memory and the buffer sit in one ATS:

```
H = ω_a a†a + ω_b b†b − 2 E_J cos(φ_Σ) cos(φ̂ + φ_Δ)
φ̂ = φ_a (a + a†) + φ_b (b + b†)
```

Bias φ_Δ = π/2 and φ_Σ = −π/2 + x, with the pump x = ε_p cos(ω_p t). Then
cos(φ_Σ) = sin(x) and cos(φ̂ + π/2) = −sin φ̂, so the ATS term is

```
−2 E_J cos(φ_Σ) cos(φ̂ + φ_Δ) = +2 E_J sin(x) sin φ̂.
```

There is no static ATS piece at this bias: sin(ε_p cos ω_p t) has only odd
harmonics of the pump. To first order in ε_p it is 2 E_J ε_p cos(ω_p t) sin φ̂.
The replacement sin(ε_p cos θ) = 2 J_1(ε_p) cos θ + … corrects the fundamental by
ε_p²/8 ≈ 1.5×10⁻⁴, which we keep in the displaced-frame averages and drop in the
closed form for g₂.

Parameters, with ω₀/2π = 0.8 GHz: (ω_a, ω_b, ω_p) = (5, 6, 4) ω₀, so 4.0, 4.8 and
3.2 GHz, and ω_p = 2 ω_a − ω_b. E_J/2π = 40 GHz, φ_a = 0.06, φ_b = 0.3.
Φ = φ_a² + φ_b² = 0.0936 and e^{−Φ/2} = 0.954278.

## 2. Normal ordering

Baker–Campbell–Hausdorff, mode by mode, with [i φ a†, i φ a] = φ²:

```
e^{i φ̂} = e^{−Φ/2} e^{i φ_a a†} e^{i φ_a a} e^{i φ_b b†} e^{i φ_b b}.
```

sin φ̂ is the odd part. Only odd total degree n = p+q+r+s survives, and the
coefficient of a†^p a^q b†^r b^s is real:

```
c = e^{−Φ/2} i^{n−1} φ_a^{p+q} φ_b^{r+s} / (p! q! r! s!).
```

Checked against a 30×30 matrix of sin φ̂: every vacuum matrix element through
order 7 agrees to 10⁻⁸, and the one element that becomes g₂,
⟨0_a, 1_b| sin φ̂ |2_a, 0_b⟩ = √2 c(0,2,1,0), agrees as well.
c(0,2,1,0) = −e^{−Φ/2} φ_a² φ_b / 2.

## 3. Which terms the pump can make static

Move to the frame rotating at ω_a and ω_b. The monomial a†^p a^q b†^r b^s then
rotates at (p−q) ω_a + (r−s) ω_b. In units of 0.8 GHz that is 5(p−q) + 6(r−s).
The fundamental of the pump cancels that rotation only when the integer is ±4.

Through order 7 the only solutions are the a²b† family and its conjugate:
(p−q, r−s) = (−2, +1) or (+2, −1). There are 12 of them
`rec:t2_4a.resonant_terms.sym.circuit=12`:

| (p, q, r, s) | operator | order |
|---|---|---|
| (0, 2, 1, 0), (2, 0, 0, 1) | a²b†, a†²b | 3 |
| (1, 3, 1, 0), (3, 1, 0, 1) | a†a³b† and h.c. | 5 |
| (0, 2, 2, 1), (2, 0, 1, 2) | a²b†(b†b) and h.c. | 5 |
| (2, 4, 1, 0), (4, 2, 0, 1) | a†²a⁴b† and h.c. | 7 |
| (1, 3, 2, 1), (3, 1, 1, 2) | a†a³b†(b†b) and h.c. | 7 |
| (0, 2, 3, 2), (2, 0, 2, 3) | a²b†(b†b)² and h.c. | 7 |

Every other odd monomial misses the pump by at least one unit of 0.8 GHz.
3 ω_p = 2 ω_b, which would resonate with b†², but sin φ̂ is odd, so that
operator is absent. Higher pump harmonics (J₃, J₅, …) plus the displacement can
make a few even or high-order monomials static: a†⁴b² at 2 ω_p (about 4×10⁻⁶ MHz),
a²b³ at 7 ω_p and a²b†⁵ at 5 ω_p (below 10⁻⁹ MHz). They are negligible next to g₂.

## 4. g₂, the one-half, and the sign

The pump splits as cos(ω_p t) = (e^{i ω_p t} + e^{−i ω_p t})/2, and only one half
is static on a²b†. Counting the same term from φ³/3! gives the same factor:
2 (from 2 E_J) × ½ (one side of the cosine) × 3 (which of the three factors is
the buffer) × 1/6 = ½. So

```
g₂ = 2 E_J ε_p × ½ × c(0,2,1,0) = −½ E_J ε_p φ_a² φ_b e^{−Φ/2}.
```

At the prompt's ε_p = 0.035 this is −0.7214 MHz
`rec:t2_4a.g2.sym.circuit=-0.7214`, not −0.763. The e^{−Φ/2} is why: the prompt's
formula g₂ = ½ E_J ε_p φ_a² φ_b drops it, and ε_p = 0.03702 restores 0.763 MHz
before any displacement. The iQuHACK tutorial drops both the ½ and e^{−Φ/2}
(g₂ = E_J ε_p φ_a² φ_b). At our operating point that overstates |g₂| by 2.13.

g₂ is negative. With the buffer drive −ε_d (b + b†) one has α² = ε_d / g₂ < 0, so
the cat lies on the imaginary axis (Re⟨a²⟩ < 0). A pump phase of π sends
cos(ω_p t + π) → −cos(ω_p t), flips g₂, and does not flip the Stark shift, which
is second order in the pump. Flipping the sign of ε_d does the same job. Either
is a gauge. The `extra_H` recipe below is written for the positive-g₂ gauge
(pump phase π), which is the one the rest of the project uses.

## 5. Displace first, then drop the fast terms

The order-1 piece is an off-resonant drive, not a small correction. On the memory
it is about 2π × 80 MHz at a detuning of 0.8 GHz; on the buffer, about 2π × 400 MHz
at 1.6 GHz. The classical amplitudes that follow are |ξ_a| ≈ 0.11 and |ξ_b| ≈ 0.30.
κ is left out of ξ: κ_b / 2Δ ∼ 10⁻³.

Solve i ξ̇ = ω ξ + F(t) on one period of 0.8 GHz (1.25 ns). The force is the
linear piece of the displaced sine,

```
F_a(t) = 2 E_J sin(ε_p cos ω_p t) e^{−Φ/2} φ_a cos φ_cl(t),
φ_cl = 2 φ_a Re ξ_a + 2 φ_b Re ξ_b,
```

and the same with φ_b, ω_b for the buffer. Iterate from cos φ_cl = 1. At ε_p = 0.035
the first pass peaks at 0.1113 and 0.3006; the fixed point is 0.1098 and 0.2967.
The pole bins k = −5 and k = −6 are empty (the pump only makes multiples of 4), so
a periodic solution exists. Once ξ matches F(φ_cl), the linear term cancels at
every sample, not only on average: the leftover is below 10⁻⁹ MHz.

Shifting a → a + ξ is the same as φ̂ → φ̂ + φ_cl, and the normal-ordered weight
picks up sin(φ_cl + n π/2) instead of i^{n−1}. The static coefficient of a
monomial is the period average of that weight times e^{i (5 Δa + 6 Δb) ω₀ t}.
Number-conserving monomials all share one average,

```
C₂ = 2 E_J ⟨sin(ε_p cos ω_p t) sin φ_cl⟩,
```

and then, with the convention H ⊃ kerr · a†²a² + chi · a†a b†b
(so the other common convention K in −(K/2) a†²a² is K = −2 kerr):

```
stark_a = −C₂ e^{−Φ/2} φ_a²          stark_b = −C₂ e^{−Φ/2} φ_b²
kerr_a  =  C₂ e^{−Φ/2} φ_a⁴ / 4       kerr_b  =  C₂ e^{−Φ/2} φ_b⁴ / 4
chi_ab  =  C₂ e^{−Φ/2} φ_a² φ_b²
```

The five ratios are exact (one and the same C₂) and come out positive for the
Stark shifts: the pump pushes both frequencies up. A linear-response estimate
C₂ ≈ −2 E_J² ε_p² e^{−Φ/2} Σ_i 2 φ_i² ω_i / (ω_i² − ω_p²) lands within 3% of the
self-consistent value (the record tolerance is 5%).

|ξ| grows with ε_p, and cos φ_cl < 1 weakens g₂, so the pump that restores
|g₂| = 0.763 MHz is a bit above 0.03702. That operating point is

```
ε_p* = 0.03761
```

and the shifts there are

| quantity | value (MHz) | record |
|---|---|---|
| stark_a | 1.053 | `rec:t2_4a.stark_a.sym.circuit=1.053` |
| stark_b | 26.33 | `rec:t2_4a.stark_b.sym.circuit=26.33` |
| kerr_a | −9.479×10⁻⁴ | `rec:t2_4a.kerr_a.sym.circuit=-9.479e-4` |
| kerr_b | −0.5924 | `rec:t2_4a.kerr_b.sym.circuit=-0.5924` |
| chi_ab | −0.09479 | `rec:t2_4a.chi_ab.sym.circuit=-0.09479` |

In the −(K/2) a†²a² convention, K_b/2π = −2 × kerr_b = 1.185 MHz. Ferrari's
"realistic" numbers are K_b/2π = 1 MHz and χ/2π = 0.5 MHz. Ours is a similar
buffer Kerr and a five-times-smaller cross-Kerr. Memory Kerr is sub-kilohertz
and does not matter. The g₂ family at ε_p*, relative to the bare a²b† coefficient,
is fixed by the zero-point phases alone (the time average cancels):
a†a³b† / g₂ = −φ_a²/3 = −0.0012, and a²b†(b†b) / g₂ = −φ_b²/2 = −0.045.
On |n_a = 4.41, n_b = 0⟩ the dressed exchange is 0.997 times the bare g₂.
Number dressing of g₂ is not the effect that moves the cat. The buffer Stark
shift is.

## 6. What has to be retuned

In the frame of the bare ω_a, ω_b the levels that a²b† connects pick up
2 stark_a + 2 kerr_a on |2, 0⟩ and stark_b on |0, 1⟩. The pump that sits on
that transition is

```
ω_p' = ω_p + 2 stark_a − stark_b + 2 kerr_a
ω_p'/2π = 3.17577 GHz = 3.2 GHz − 24.23 MHz.
```

The buffer drive has to move with the buffer: ω_b + stark_b, that is 4.82633 GHz,
26.33 MHz above 4.8 GHz. That is ten times κ_b/2π = 2.6 MHz, so a drive left at
the bare ω_b does not inflate a cat. The Stark terms are then omitted from
`extra_H`: they have been absorbed into the two frequencies. Kerr and cross-Kerr
stay, and they do not care about the pump phase.

Leaving the pump at 3.2 GHz detunes the |2, 0⟩ ↔ |0, 1⟩ exchange by those
24 MHz. With G = √2 |g₂| ≈ 2π × 1.079 MHz the resonant swap takes 0.232 µs, and
the bare-pump transfer tops out near 4G²/(4G²+δ²) ≈ 0.008. The retuned pump is
what `tasks/task_2_4a.py --part tdsim` integrates (section 9).

## 7. How a readout drive enters

Three ways a tone can be applied. Only the flux tone makes new resonant operators.

(a) Capacitive drive on the memory, 2 ε_Z cos(ω_r t) (a + a†), with
ω_r = ω_a + stark_a. In the frame of the shifted memory this is ε_Z (a + a†)
plus a counter-rotating piece at 2 ω_a. The Bloch–Siegert shift ε_Z² / 2 ω_a is
7×10⁻⁵ MHz when ε_Z = g₂. Negligible. This is the drive the effective model
already uses. It has to follow the 1 MHz memory Stark shift: 1 MHz is not small
next to g₂.

(b) A second ATS flux, x → ε_p cos(ω_p t) + ε_r cos(ω_r t). To first order in
ε_r the added piece is 2 E_J ε_r cos(ω_r t) cos(ε_p cos ω_p t) sin(φ̂ + φ_cl).
At ω_r = ω_a and ε_r ≈ 3.33×10⁻⁴, the linear term equals ε_Z = g₂. The same
cubic that dresses g₂ then gives

```
−(φ_a²/2) ε_Z  a† a² ,    −φ_b² ε_Z  a b† b.
```

Those ratios are exact with or without the displacement. The displacement adds
one more: a beam-splitter g_bs (a b† + a† b) with

```
g_bs / ε_Z = 0.03089
```

at ε_p*. It is exactly resonant, including after the Stark retuning, because
ω_a − ω_p = ω_b − ω_a (= 0.8 GHz) and both modes are shifted by amounts that
preserve that equality at this order. The extra memory loss is 4 g_bs² / κ_b.
At ε_Z = 3 g₂ that is 0.048/µs, the same size as κ_a = 0.058/µs. This is the
term 2.4b and 2.4c have to decide about. It is off in the undisplaced theory:
a b† is 0.8 GHz off a tone at ω_a until the pump's ξ supplies the missing quantum.

(c) The buffer drive itself, if it is a flux tone at ω_b rather than a capacitive
drive. Then g_sp = −(φ_b²/2) ε_d = −0.045 ε_d multiplies (b†² b + b† b²). That is
Réglade's g_sp. The same displacement converts a sliver of it into a memory
two-photon drive, 6.2×10⁻⁴ ε_d (a² + h.c.). Small next to g₂, worth knowing
about, not worth fitting.

## 8. What this is in the parasitic catalogues

Réglade's g_lin (b + b†) is our order-1 pump term. Here it is off-resonant, so it
is already included as ξ_b and as the Stark shifts; a resonant linear tone is
cancelled by driving the opposite tone, which is their procedure and not needed
for our pump. Réglade's g_sp and the spurious Kerr are (c) and the C₂ formulas.
Ferrari's cross-Kerr is our chi_ab. Their saturation story still applies; the
number to put in is 0.095 MHz, not 0.5.

## 9. The check against a time-dependent integration

`circuit_rotating_H` keeps every odd monomial through order 5, including the
order-1 drive, in the bare rotating frame. It does not pre-displace: ξ is only
used to prepare the initial state and to read the observables, so the integration
is an independent test of section 5. Terms smaller than 2π × 100 Hz are dropped.
The solver is Tsit5 with rtol 10⁻⁸, atol 10⁻¹⁰, and a step cap of 10⁷, because
the fastest pieces sit near 8 GHz.

Two runs, both at ε_p*, Na = 10, Nb = 8, for 0.3 µs, from the displaced Fock
state D(ξ_a) D(ξ_b) |2, 0⟩ with the linear-response ξ:

- Bare pump at 3.2 GHz. The exchange should stall, max P(|0, 1⟩) ≲ 0.05.
- Pump at ω_p'. The exchange should complete, max P ≥ 0.95, and the fitted
  |g₂| should land within 3% of 0.763 MHz. The no-½ curve (2.13 times larger)
  is drawn on the same figure and should miss by many standard deviations.
  If the first retune falls short of 0.95, the script shifts ω_p by the fitted
  detuning once and reports that shift as the second-order piece. A rerun at
  rtol 10⁻¹⁰ must move P by less than 10⁻⁴, and the fit must agree between
  (Na, Nb) = (8, 8) and (10, 6).

The inflation check is 0.2 µs from the displaced vacuum, |α|² = 1 so ε_d = g₂,
jumps √κ_b b and √κ_a a, Na = 12, Nb = 6. ⟨n_a⟩ and the buffer amplitude in the
Stark-shifted frame are compared with `two_mode` at g₂ = g₂,disp < 0: E0 with
nothing extra, E1 with the Kerr and cross-Kerr of section 5, E2 with the
tutorial g₂ and the same ε_d. E1 should track the circuit (max |Δn_a| ≤ 0.03);
E2 should be at least five times worse. Re⟨a²⟩ in the circuit run should be
negative. The α = 2.1 inflation (Na = 16, Nb = 12) is a queued job, not this run:
at that amplitude the buffer fills too far for Nb = 6.

Figure: `figures/task_2_4a_validation.png`.

## 10. What is left out

Second-order RWA (van Vleck) was not computed; the recalibration in section 9 is
the numerical stand-in, and only if the first retune is short of 0.95. κ is not
in ξ. Orders above 7 in the term table, and above 5 in the integration, are
dropped; the order-7 family is already below a kilohertz except for the b†b
dressing of g₂, which the table keeps. No lab-frame simulation over microseconds.
No sweep of Γ_X: that is 2.4b, using the recipe in section 11.

## 11. Pump-term table at ε_p*

Static coefficient in the displaced frame, MHz. "Freq" is (p−q)ω_a + (r−s)ω_b
in units of 0.8 GHz, then in GHz. Resonant means sitting on ±ω_p.

| term | order | ×0.8 GHz | GHz | coefficient (MHz) | resonant? |
|---|---|---|---|---|---|
| a²b† | 3 | −4 | −3.2 | −0.763 | yes |
| a†²b | 3 | +4 | +3.2 | −0.763 | yes |
| a†a³b† | 5 | −4 | −3.2 | +9.16×10⁻⁴ | yes |
| a² b† (b†b) | 5 | −4 | −3.2 | +0.0343 | yes |
| a†²a⁴b† | 7 | −4 | −3.2 | −4.12×10⁻⁷ | yes |
| a†a³b† (b†b) | 7 | −4 | −3.2 | −4.12×10⁻⁵ | yes |
| a² b† (b†b)² | 7 | −4 | −3.2 | −5.15×10⁻⁴ | yes |
| a, a† | 1 | ∓5 | ∓4.0 | ~0 | no (0.8 GHz off, and cancelled by ξ) |
| b, b† | 1 | ∓6 | ∓4.8 | ~0 | no |
| a†a | 2 | 0 | 0 | +1.053 | static Stark, not a ±ω_p resonance |
| b†b | 2 | 0 | 0 | +26.33 | static Stark |
| a†²a² | 4 | 0 | 0 | −9.48×10⁻⁴ | static Kerr |
| b†²b² | 4 | 0 | 0 | −0.592 | static Kerr |
| a†a b†b | 4 | 0 | 0 | −0.0948 | static cross-Kerr |
| ab† | 2 | +1 | +0.8 | ~0 from the pump | no; the flux tone makes it resonant |
| a†a² | 3 | −5 | −4.0 | ~0 from the pump | no; flux tone: −(φ_a²/2) ε_Z |
| b†b² | 3 | −6 | −4.8 | ~0 from the pump | no; flux tone at ω_b: −0.045 ε_d |
| a b†b | 3 | −5 | −4.0 | ~0 from the pump | no; flux tone: −φ_b² ε_Z |

Conjugates carry the same coefficient and the opposite frequency. The full list
through order 7 is `results/arrays/t2_4a.resonant_terms.sym.circuit.npz`.

## 12. extra_H for the readout and bit-flip lanes

Stark shifts are intentionally absent: the pump and the buffer drive are retuned.
Kerr and cross-Kerr do not change when the pump phase is flipped to make g₂ positive.

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
# Flux-tone readout option: add g_bs*(a@b.dag() + a.dag()@b) with g_bs = 0.03089 * eps_z.
```
