# Building a cat qubit one ingredient at a time

**DuQuantum 2026 · Alice & Bob challenge · Introductory Track**
Team: Pranav <!-- add full names -->

> **Two layers.** This README is the short version for everyone.
> [`TECHNICAL.md`](TECHNICAL.md) is the detailed layer for judges, reviewers and AI agents: every claim, the number behind it, the file that produced it, and how we checked it.

## The idea in one minute

A normal qubit can fail in two ways: its 0 and 1 can swap (a **bit flip**), or the sign of a superposition can flip (a **phase flip**). Error correction has to fight both, which costs a lot of hardware.

Alice & Bob store a qubit in a microwave resonator as one of two "blobs" of light, at **+α** and **−α**. A carefully designed leak removes and adds photons **only in pairs**, which turns the resonator into two valleys that trap the light. Jumping between valleys (a bit flip) becomes exponentially rare, so only phase flips are left to correct. This is a **cat qubit**.

We simulated how that trap forms, starting from the simplest possible model and adding one ingredient at a time. Each time, we predicted the answer by hand first and then checked it.

## What we found

| Step | What we did | What we found |
|---|---|---|
| **1.0** Warm-up | One resonator: add photon leakage, then pair leakage, then pair pumping | All three match the hand predictions exactly. Pair leakage stalls at 0.4998 photons, because pairs can never remove the last odd photon. |
| **1.1** Real circuit | Add the second "buffer" resonator that creates the pair leak in hardware | The photon number **overshoots by ~56%** before settling, because the buffer is too slow for the simple model's shortcut. It still settles at the right value (4.40 photons). |
| **1.2** Can we trust it? | Make the simulation bigger, one resonator at a time, until the answer stops changing | The starter settings get the final value right but **miss the overshoot by 11%**. The buffer needs **10+ levels** instead of 6, because it briefly holds ~2 photons. |
| **1.3a** What did we make? | Track parity, fidelity, purity and coherence | We made the **even cat** (both valleys at once, not one or the other). Photon loss fades it into a plain mixture in **~1.9 µs**, as predicted. |
| **1.3b/c** One definite state | Give the memory a short push toward +α before the pump turns on | Lands in the **+α** valley with **99.9%** fidelity (above 99% in under half a microsecond). The stabilization forgives a sloppy push: a 30° aiming error still gives 99.5%, where the push alone would give 31%. Pushing in the wrong direction picks no valley at all. |

![Two-mode inflation](figures/task_1_1_inflation.png)
*Left: the memory photon number overshoots, then settles at α² = 4.41 (grey line). The simple one-mode model (dotted) rises smoothly. The starter simulation size (dashed) underestimates the overshoot. Right: how much population leaks into the highest levels the computer keeps. Smaller is better.*

![Convergence](figures/task_1_2_convergence.png)
*The final value (orange) doesn't care about simulation size. The overshoot peak (blue) needs about 24 memory levels and about 10 buffer levels.*

![Logical state preparation](figures/task_1_3b_logical_prep.png)
*Left: starting from a displaced state, the memory settles into |+α⟩. Middle: with stabilization (blue) the result barely depends on the push's aiming error; the push alone (orange) would need to be almost perfect. Right: pushing during inflation also works if the push is strong; the wrong drive direction (dashed) picks no valley.*

## Run it yourself

```bash
pip install -r requirements.txt
./run_all.sh              # every figure and number, ~15-25 min on a laptop
```

Or open the notebooks, one per task, in order: [`notebooks/`](notebooks/). Each one explains the task in plain words, runs the same code as `run_all.sh`, and shows the results. The convergence sweep (Task 1.2) is the only slow step, so its notebook loads saved results by default.

## How we used AI

We used AI assistants to learn the background, plan the project, and write much of the code in `src/` and `tasks/` (Claude). <!-- add Cursor/Grok here if you use them --> Every number we report is produced by the scripts in this repo and checked against a hand prediction or a convergence test. We can explain each one. We also ran an independent AI code review focused on physics mistakes (missing 2π, signs, convergence) with [`tools/ai_review.py`](tools/ai_review.py). Details are in [`TECHNICAL.md`](TECHNICAL.md#ai-use).

## Repo map

```
README.md          you are here (human layer)
TECHNICAL.md       detailed layer: claims, methods, checks, file map
notebooks/         one notebook per task (01 to 05)
tasks/             the scripts the notebooks call (task_1_0.py ... task_1_3b.py)
src/               shared code: parameters, models, analysis helpers
results/           every reported number, as JSON
figures/           every figure
tools/             AI code-review helper
docs/              the original challenge prompt
```
