# Cat qubits: bit flips, phase flips and a better readout

**DuQuantum 2026 · Alice & Bob challenge · Standard Track**
Team: Pranav Reddy, Harshit Aggarwal, Halo Kwok, Xuanyu Zhu

> **Two layers.** This README and the figures are the human layer: plain words, the main results, and pictures.
> The detailed layer for judges, reviewers and AI agents (every claim, the number behind it, the file that produced it, and how we checked it) is [`docs/SECTION2.md`](docs/SECTION2.md) for the Standard-track tasks and [`TECHNICAL.md`](TECHNICAL.md) for the Section 1 groundwork.

Completed: **Tasks 1.0(a–c), 1.1, 1.2 and 1.3(a–c)**. We use the supplied parameters with $\alpha=2.1$, time in µs, a single-mode cutoff $N=30$, and two-mode cutoffs $(N_a,N_b)=(32,12)$ unless specified otherwise. [Methods and numerical evidence](TECHNICAL.md) · [Challenge prompt](docs/challenge_prompt_v4.md)

## 1.0 — Add dissipation one ingredient at a time

Alice & Bob store a qubit in a microwave resonator as one of two "blobs" of light, at **+α** and **−α**. A carefully designed leak removes and adds photons **only in pairs**, which turns the resonator into two valleys that trap the light. Jumping between valleys (a bit flip) becomes exponentially rare, so only phase flips are left to correct. This is a **cat qubit**.

The Standard track asks four questions about this qubit. Here they are in plain words.

- **How rarely does it bit-flip? (2.1)** Think of a ball in one of two valleys. Tiny random kicks (lost photons) almost never carry it over the hill. "Almost never" here means seconds, which is far too long to simulate step by step. So we don't wait for the ball. Every way the system can relax has its own fixed rate, like a guitar string has its own notes, and the slowest one *is* the bit-flip rate. We compute that note directly, then check it against brute-force simulation where both are possible. We also found that the ball escapes in two different ways, which is why the textbook scaling law bends.
- **How often does it phase-flip? (2.2)** Every lost photon flips the cat's "even/odd" label. More photons means more losses, so phase flips grow in proportion to the photon number, exactly as predicted.
- **How do you read it? (2.3)** Nudge the memory gently. It pushes on the buffer, and the buffer's leaking light tells you which valley the ball is in. Memory and buffer act like two coupled springs, so the signal *rings* at 3.2 MHz before it settles.
- **How do you read it better? (2.4)** Push a swing at its own rhythm and a small push goes a long way. A readout drive at the ring frequency gets more signal for the same disturbance, and a gradient optimizer improves it further. We also simulated the real circuit and found that the pump must be retuned by 23 MHz, or the photons don't pair up.

Each time, we predicted the answer by hand first and then checked it numerically, at two or more simulation sizes.

## What we found: Section 2 (Standard track)

Our one idea: every decay rate is an **eigenvalue** of the Lindblad equation, so we compute bit-flip times of seconds in about a minute instead of simulating for seconds, and check them against direct simulation where that is possible.

| Task | What we did | What we found |
|---|---|---|
| **2.1** Bit-flip rate Γ_X | The prompt's method (fit the decay of Re⟨a⟩) at α ≤ 1.4, and the slowest eigenvalue of the "odd" half of the Lindblad matrix up to α = 2.5 | The two methods agree to 2e-8. Γ_X falls from 2.3e-3 to 3.1e-8 per µs (α = 1.0 to 2.4; 2.6 s between flips at α = 2.1). Fitted **γ = 2.30**, but it is not one number: it drifts from 3.1 to 1.9, reaching the deck's γ ≲ 2 only at large α, because **two flip mechanisms** take turns. The naive Golden Rule estimate gives γ = 4 and describes only the first; a κ_a sweep proves the hand-over (slope 1.06 → 2.05). |
| **2.2** Phase-flip rate Γ_Z | Parity decay from the even cat (the prompt's method) and the slowest nonzero eigenvalue of the "even" half | Slope 0.991 × 2κ_a; at α = 2.1, Γ_Z = 0.5146 per µs. The two methods agree to 5 digits. |
| **2.3** Readout through the buffer | Drive the memory, watch the buffer field | The signal matches our linear formula to 1% and **rings at 3.2 MHz** (the same oscillator as the Task 1.1 overshoot); it settles in 1 µs. |
| **2.4** Better readout | Expanded the circuit Hamiltonian term by term and simulated it without the rotating-wave shortcut; measured flip cost vs signal; compared pulse shapes; optimized the pulse with gradients through the simulator | (a) The pump amplitude must be 0.037, not 0.035, and the pump must be **retuned by −23 MHz**: at the nominal frequency, Stark shifts stop the photon-pair conversion in our circuit simulation. (b) Signal and extra bit flips both grow as ε_Z², so turning up the drive buys nothing per unit of information; only the pulse's *shape* helps. (c, d) A drive at the 3.2 MHz ring frequency cuts the readout error 1.7× (1.12% → 0.65% in 2 µs); a gradient-optimized pulse gives **40% more signal with 10% fewer bit flips** than a square pulse at α = 2.1, and 1.3–1.7× more signal per bit flip in all 9 converged cases we ran (α = 1.4–2.1, two pulse lengths, two amplitudes). |

![Bit-flip rate](figures/s2/gamma_x.png)
*Task 2.1. Bit-flip rate against cat size (α² is the photon number). Blue: our full model, computed as an eigenvalue. Crosses: brute-force time simulation where it is still feasible; they land on the blue curve. The two straight lines are the two escape routes over the hill: green (γ = 4, the naive Golden Rule answer) wins for small cats, red (γ = 2) for large ones, which is why the blue curve bends. The simplified one-mode model (orange) underestimates the flips by about 3× at α = 2.1.*

![Readout ringing](figures/s2/readout.png)
*Task 2.3. Left: the buffer signal after the readout drive switches on (α = 2.1), divided by the linear prediction. It overshoots and rings at 3.2 MHz, then settles on the prediction (−1) within about 1 µs; two simulation sizes overlap. At ε_Z = 2 g₂ the signal drifts away because the drive itself starts flipping the qubit. Right: the steady-state signal grows in proportion to the drive, then collapses once the drive is strong enough to flip the qubit.*

![Readout pulses](figures/s2/slide_pulse_frontier.png)
*Signal vs bit-flip cost for each readout pulse shape at α = 2.1 (0.5 µs pulse). Up and to the left is better. The square pulse (dashed) is never the best choice.*

## Groundwork: Section 1

| Step | What we did | What we found |
|---|---|---|
| **1.0** Warm-up | One resonator: add photon leakage, then pair leakage, then pair pumping | Photon loss and pair loss match the hand formulas to 10⁻¹¹ or better; pair pumping settles within 0.5% of the prediction. Pair leakage stalls at 0.4998 photons, because pairs can never remove the last odd photon. |
| **1.1** Real circuit | Add the second "buffer" resonator that creates the pair leak in hardware | The photon number **overshoots by ~56%** before settling, because the buffer is too slow for the simple model's shortcut. It still settles at the right value (4.40 photons). |
| **1.2** Can we trust it? | Make the simulation bigger, one resonator at a time, until the answer stops changing | The starter settings get the final value right but **miss the overshoot by 11%**. The buffer needs **10+ levels** instead of 6, because it briefly holds ~2 photons. |
| **1.3a** What did we make? | Track parity, fidelity, purity and coherence | We made the **even cat** (both valleys at once, not one or the other). Photon loss fades it toward a plain mixture with a **1.95 µs** lifetime (predicted 1.94 µs); by 6 µs it is essentially a mixture. |
| **1.3b/c** One definite state | Give the memory a short push toward +α before the pump turns on | Lands in the **+α** valley: above **99%** fidelity within 0.4–0.5 µs, and **99.9%** by 2 µs. The stabilization forgives a sloppy push: a 30° aiming error still gives 99.5% (the push alone would give 31%), and the 99% limit is about ±35°. Pushing in the wrong direction picks no valley at all. |

![Two-mode inflation](figures/task_1_1_inflation.png)

**Two-mode inflation.** (a) Memory and buffer occupations at $(32,12)$, with the memory at $(24,6)$ (start) dashed and the effective model dotted. The horizontal line marks $\alpha^2$. (b) Full-range top-level probabilities over 0–3 µs: $p_a^{(2)}$ sums the highest two memory levels; $p_b^{(1)}$ is the highest buffer level. Solid curves use $(32,12)$ and dashed curves $(24,6)$. The dotted line marks the chosen **0.1% tolerance**. The $(24,6)$ buffer reaches **4.62%**; both $(32,12)$ monitors remain below the tolerance throughout inflation.

![Two-mode memory inflation](figures/task_1_1_wigner.gif)

**Memory phase-space evolution.** The reduced memory state at $(32,12)$ evolves from vacuum into two lobes with interference over 0–3 µs, with a fixed color scale. [Static snapshots](figures/task_1_1_wigner.png). Independent integration and timestep checks reproduce the ringdown; [numerical audit](figures/task_1_1_numerical_checks.png).

## 1.2 — Check semiclassical agreement and convergence

The reference calculation at $(40,14)$ gives a late-time occupation of **4.4026**, only **0.167% below** $\epsilon_d/g_2=4.41$. Steady occupation is much less sensitive to truncation than the transient peak.

Both the trajectory sweeps and the scalar convergence plot use the same slices: vary $N_a$ at **$N_b=14$**, then vary $N_b$ at **$N_a=40$**.

![Separate cutoff sweeps](figures/task_1_2_cutoff_sweeps.png)

**Cutoff dependence during inflation.** (a,c) Sweep $N_a$ at $N_b=14$; (b,d) sweep $N_b$ at $N_a=40$. Upper and lower rows show memory and buffer occupations. Colors identify the varied cutoff; black dashes show $(40,14)$ and horizontal dotted lines mark $\alpha^2$. The first 1.2 µs of each 3 µs trajectory is shown.

| Observable | Relative tolerance | Smallest tested $N_a$ at $N_b=14$ | Smallest tested $N_b$ at $N_a=40$ |
|---|---:|---:|---:|
| Steady occupation | 0.1% | **16** | **4** |
| Transient peak | 0.5% | **24** | **10** |

Each minimum must pass together with all larger cutoffs in its sweep, relative to $(40,14)$. These are separate-sweep minima. The buffer is almost empty at late times, but reaches about two photons with a substantial tail during inflation; the memory likewise needs room for the overshoot.

![Steady and transient convergence](figures/task_1_2_convergence.png)

**Observable convergence.** Peak occupation $n_{a,\mathrm{pk}}=\max_t\langle n_a(t)\rangle$ and late-time mean $\bar n_{a,\mathrm{ss}}$, averaged over 2.81–3 µs, for the same two sweeps. Dotted lines mark $\alpha^2$.

To check the quantum state as well as occupation, we compare all **36 cutoff pairs** with $(40,14)$ using maximum reduced-memory trace distance, after zero-padding the smaller Fock space. This tests both populations and coherence. Requiring $D_{\max}\leq1\%$, the occupation tolerances above, and both monitored top-level populations below 0.1% gives **$(28,12)$ as the smallest tested passing pair**, with $D_{\max}=0.848\%$. Our **chosen cutoff is $(32,12)$**, used throughout Tasks 1.1 and 1.3, with additional margin at $D_{\max}=0.310\%$. Each passing pair must also have all larger tested pairs pass.

![Joint memory-state convergence](figures/task_1_2_error_grid.png)

**Joint memory-state convergence.** Axes give the retained memory and buffer dimensions $N_a$ and $N_b$. Blue shading shows $D_{\max}=\max_t\tfrac12\|\rho_a(t)-\rho_{a,\mathrm{ref}}(t)\|_1$ relative to $(40,14)$, where $\rho_a$ is the reduced memory state and smaller states are zero-padded. Lighter shades mean smaller differences; the color bar is logarithmic in percent, with a 0.1% display floor. Small circles mark the 36 computed pairs. The black curve is the **$D_{\max}=1\%$ threshold**; the upper-right side satisfies the state-distance criterion. The black ring marks the chosen cutoff $(32,12)$, used throughout Tasks 1.1 and 1.3; the star marks reference $(40,14)$, where $D_{\max}=0$. Background and contour use the same shape-preserving interpolation; cutoff checks use computed values. Each distance is maximized over 301 saved times from 0 to 3 µs.

## 1.3(a) — Identify the prepared state and its decay

Memory parity $\Pi=(-1)^{a^\dagger a}$ commutes with the two-photon Hamiltonian and buffer loss. Vacuum has parity $+1$, so without single-photon memory loss the stabilized state approaches the even cat $\lvert C_+\rangle\propto\lvert\alpha\rangle+\lvert-\alpha\rangle$. Finite $\kappa_a$ changes parity and produces a progressively mixed state.

| Time (µs) | $\langle\Pi\rangle$ | $F_+=\langle C_+\rvert\rho_a\lvert C_+\rangle$ | Purity $\mathrm{Tr}(\rho_a^2)$ | $C=2\lvert\langle\alpha\rvert\rho_a\lvert-\alpha\rangle\rvert$ |
|---:|---:|---:|---:|---:|
| 1 | 0.629 | 0.811 | 0.692 | 0.626 |
| 6 | 0.0483 | 0.524 | 0.501 | 0.0484 |

At 1 µs, the large matrix element $C$ and [Wigner interference fringes](figures/task_1_3a_wigner_fading.gif) demonstrate coherence between the lobes. An equal incoherent mixture has $C=2e^{-2\alpha^2}\approx0.00030$. By 6 µs the state approaches that mixture.

![Decay of memory-state interference](figures/task_1_3a_wigner_fading.gif)

**Interference decay.** Reduced-memory Wigner evolution over 1–6 µs at $(32,12)$. The fixed color scale makes the declining fringe contrast directly comparable. [Static snapshots](figures/task_1_3a_wigner_fading.png) · [Diagnostic curves](figures/task_1_3a_cat_diagnostics.png).

The fitted rate is **$\Gamma=0.5135$ µs⁻¹**, compared with $2\kappa_a\langle n_a\rangle_{\mathrm{ss}}=0.5146$ µs⁻¹. The corresponding parity-decay time is **1.95 µs**; interference weakens continuously over this timescale.

## 1.3(b) — Prepare a definite logical state

A real memory displacement breaks the symmetry between $\pm\alpha$. Starting from $\lvert\beta\rangle_a\lvert0\rangle_b$ with $\beta>0$ and then enabling stabilization selects $\lvert+\alpha\rangle$. Buffer-only control preserves the memory parity symmetry and cannot select a sign from vacuum.

We also apply $i\varepsilon_1(a^\dagger-a)$ during the first 0.1 µs of inflation. The orthogonal drive $\varepsilon_1(a+a^\dagger)$ serves as a control.

| Protocol | $F_\alpha(2\,\mathrm{\mu s})$ | $\mathrm{Re}\langle a\rangle/\alpha$ at 2 µs | $t_{99}$ (µs) |
|---|---:|---:|---:|
| Displace first, $\beta=1.5$ | **0.99878** | 0.99679 | **0.41** |
| Drive during inflation, $\varepsilon_1=20$ µs⁻¹ | 0.99681 | 0.99290 | 0.67 |
| Orthogonal drive, $\varepsilon_1=10$ µs⁻¹ | 0.49999 | 0 | — |

Here $F_\alpha=\langle\alpha\rvert\rho_a\lvert\alpha\rangle$; $t_{99}$ is the first saved time after which fidelity stays above 0.99 through 2 µs. For displaced starts, the clock begins after the idealized displacement pulse.

![Logical-state preparation](figures/task_1_3b_logical_prep.png)

**Logical-state preparation.** (a) Fidelity from real displaced starts. (b) Stabilized fidelity at 2 µs versus the initial overlap for $\beta=\alpha e^{i\phi}$. Dotted guides mark 0.99. (c) Mean amplitude under the finite-duration drive; shading marks its 0–0.1 µs interval, and legend values give $\varepsilon_1$ in µs⁻¹.

## 1.3(c) — Cost of preparation

- **Control:** a resonant memory drive, adding a control channel or reusing an existing one.
- **Calibration:** amplitude and phase referenced to the stabilization pump. At a tested phase error of 30°, stabilization gives **99.51%** fidelity, versus **30.68%** initial overlap; at 45° the stabilized fidelity falls to 97.27%.
- **Dynamics and time:** displace first, then stabilize to avoid a competing drive during inflation. The $\beta=1.5$ protocol reaches 99% after 0.41 µs of stabilization, in addition to the displacement pulse. Driving during inflation raises the sampled memory peak to 8.51 photons.

## Reproduce the results

```bash
pip install -r requirements.txt
./run_all.sh              # every figure and number, ~30-40 min on a 4-core laptop
```

Section 2 results are all saved as JSON, so checking a claim needs no re-run. `python -m research.s2.summarize` rebuilds every Section 2 table and figure from them in about a minute. The commands for re-running each kind of computation are in [`docs/SECTION2.md`](docs/SECTION2.md#reproduce).

Unit tests: `python -m unittest discover -s tests -v`. The Section 1 convergence grid resumes cached calculations; redraw its figures with `python -m tasks.task_1_2 --plot-only`. Every Section 1 figure and the four Wigner animations (GIF) have a caption in [`figures/CAPTIONS.md`](figures/CAPTIONS.md), and the full Section 1 write-up with all numbers is [`docs/SECTION1.md`](docs/SECTION1.md).

For Section 1, you can also open the notebooks, one per task, in order: [`notebooks/`](notebooks/). Each one explains the task in plain words, runs the same code as `run_all.sh`, and shows the results. The convergence sweep (Task 1.2) is the only slow step, so its notebook loads saved results by default.

## AI use

We used AI assistants to learn the background, plan the project, and write much of the code in `src/`, `tasks/` and `research/s2/` (Claude), and to run the cloud batches on Vultr. Claude Code did most of the implementation. Vultr VMs ran the large batches of JAX/dynamiqs simulations. The Gemini API served as an independent physics checker of the code and, through its multimodal input, of the plots, until the free tier was exhausted overnight. Cursor and a Groq-powered bot were used for the product layer (the Lab site), and Codex for Section 1 validation, convergence analysis and figure preparation. Every tool use, with its cost, is logged in [`docs/tools-log.md`](docs/tools-log.md). Every number we report is produced by the scripts in this repo and checked against a hand prediction or a convergence test. We can explain each one. For Section 2, every rate was checked two independent ways (eigenvalue vs time-domain fit, agreeing to 2e-8), every headline number at two or more truncations, and every claim in the write-up against its JSON. That self-check caught real mistakes before submission, for example a pulse result quoted next to the wrong drive amplitude. We also ran an independent AI code review focused on physics mistakes (missing 2π, signs, convergence) with [`tools/ai_review.py`](tools/ai_review.py). Details are in [`TECHNICAL.md`](TECHNICAL.md#ai-use).

## Repo map

**Human layer** (start here)
```
README.md          you are here: plain-language story and main results
figures/           every figure; figures/s2/slide_*.png are the presentation figures
notebooks/         one notebook per Section 1 task, with plain-language explanations
```

**Detailed layer** (for judges, reviewers and AI agents: every claim, its number, its file, its check)
```
docs/SECTION1.md   Section 1 write-up: every task, number and figure
docs/SECTION2.md   Section 2 write-up: methods, numbers, convergence, reproduce commands
TECHNICAL.md       Section 1 claims table, convergence study, AI-use and review log
results/           every reported number as JSON; results/s2/SUMMARY.md has all Section 2 tables
research/s2/       Section 2 code (eigen-solver, readout, pulses, optimizer, circuit simulation)
src/, tasks/       shared model code and the Section 1 task scripts
research/          Section 1 stretch studies; research/LOG.md lists every research run
cloud/             Vultr batch launcher and the job lists we ran
docs/tools-log.md  every external tool and service used, with cost
reviews/           independent AI code and figure reviews
docs/              also the original challenge prompt
```
