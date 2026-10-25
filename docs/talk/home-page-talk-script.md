# Home-page talk: 8-minute script with live demo

The home page of the site is the presentation: https://66-42-119-3.sslip.io/#/
Use ← and → to step through its 12 sections (cover, Task 1, 2.1, 2.2, 2.3, 2.4a–d, Academy, sponsors, why).
The talk is planned for 7:30, which leaves 0:30 of buffer. That's about 140 words a minute. Numbers and speaker split are the same as the submitted 4-minute walkthrough (slides/walkthrough-script.md).

## Before the clock starts (1 minute)

- **Tab 1:** the home page, at the cover.
- **Tab 2:** a second copy of the home page, already scrolled to section 11 (Sponsors). You switch to it after the demo, so you don't have to scroll back.
- Open L4 once beforehand, so the in-browser simulator is warm.
- Turn the laptop sound up and point it at the room for the narration.
- Only if you'll use Talk: allow the microphone once, before the talk.
- Fallback if the Vultr site is slow: the local stack on the Mac (site on port 5180, API on 8001).

## Running order

| # | Section | Speaker | Time | Clock |
|---|---------|---------|------|-------|
| 1 | Cover | Pranav | 0:15 | 0:15 |
| 2 | Task 1 | Philip | 0:25 | 0:40 |
| 3 | 2.1 Bit flips | Pranav | 0:30 | 1:10 |
| 4 | 2.2 Phase flips | Halo | 0:20 | 1:30 |
| 5 | 2.3 Readout | Philip | 0:25 | 1:55 |
| 6 | 2.4a The real circuit | Philip | 0:25 | 2:20 |
| 7 | 2.4b Pushing harder | Pranav | 0:20 | 2:40 |
| 8 | 2.4c Push in rhythm | Pranav | 0:20 | 3:00 |
| 9 | 2.4d Why it works | Pranav | 0:25 | 3:25 |
| 10 | Cat Qubit Academy | Harshith | 0:15 | 3:40 |
| D1 | Demo: L1 narration | Harshith | 0:35 | 4:15 |
| D2 | Demo: L4 and Ask Schrö | Harshith | 1:05 | 5:20 |
| D2+ | Talk (optional, see note) | Harshith | +0:20 | |
| D3 | Demo: L8 pulse design | Harshith | 1:00 | 6:20 |
| 11 | Sponsors | Halo | 0:25 | 6:45 |
| 12 | Why, and what's next | Pranav | 0:45 | 7:30 |

Harshith narrates the demo. Someone else can drive the laptop if that's easier.

---

## 1. Cover · Pranav · 0:15

We're the Alice & Bob standard-track team. A cat qubit stores a bit as light sitting in one of two valleys. We measured how often it fails, designed a better way to read it, and built a site that teaches all of it. This site is also our slides.

**→**

## 2. Task 1 · Philip · 0:25

First we built the cat. A buffer pumps photons in two at a time and pulls pairs back out, so the memory settles into two blobs. The stripes between them show it's a real superposition, not a 50/50 mixture. We also checked that the result doesn't depend on how many photon levels we keep: the cheaper truncation matches a much bigger one to 0.035%.

**→**

## 3. 2.1 · Bit flips · Pranav · 0:30

A bit flip is a jump from one valley to the other, and it's very rare here: the bit-flip time is 2.6 seconds at α = 2.1. Simulating that directly would take 300 million time steps, so we don't wait for it. Every way the state relaxes is an eigenvalue of the Liouvillian, and the bit flip is the slowest one, the one closest to zero. Parity symmetry halves the search, and the answer matches direct simulation to 10⁻⁸. On the right, two escape routes take over in turn as photon loss grows.

**→**

## 4. 2.2 · Phase flips · Halo · 0:20

Phase flips are the opposite story. Every lost photon flips even and odd, so the phase-flip rate grows with the number of photons: about 2κₐα². Three methods agree to 0.1%. The phase-flip time is about 2 microseconds, so phase flips happen 1.3 million times more often than bit flips.

**→**

## 5. 2.3 · Readout · Philip · 0:25

To read the bit, we nudge the memory and listen to the buffer. The two valleys give opposite signs, matching theory within 1%. The catch is that the signal rings at about 3.2 MHz for roughly a microsecond, like a damped spring. That ringing is what Task 2.4 uses.

**→**

## 6. 2.4a · The real circuit · Philip · 0:25

Here is the real Josephson circuit, with no rotating-wave approximation. We expand the sine term, and only the a²b† piece survives at the pump frequency: that's the pairing. But at the textbook pump frequency nothing happens, and the pink line stays flat. The pump itself shifts the mode frequencies, so we retune it by −23 MHz, and then the blue line follows the model.

**→**

## 7. 2.4b · Pushing harder doesn't help · Pranav · 0:20

The obvious fix for a weak signal is to drive harder. But the signal and the extra bit flips both grow as the drive strength squared. At 0.5 g₂, the bit-flip time falls from 2.6 seconds to about a millisecond while the drive is on. A harder drive doesn't buy a better trade. Only the shape of the pulse can.

**→**

## 8. 2.4c · Push in rhythm with the ring · Pranav · 0:20

So we push in rhythm with the 3.1 MHz ring, like pushing a swing at the right moment. With the same 2-microsecond pulse length, the readout error drops from 1.12% to 0.65%, with fewer bit flips.

**→**

## 9. 2.4d · Why it works · Pranav · 0:25

We didn't just guess that rhythm. We asked the model for the single best pulse, with no hint about frequency. On the left, the best pulse lines up with a cosine at the ring frequency. On the right, its spectrum peaks at 3.03 MHz, right next to the 3.14 MHz ring. A gradient optimizer with full freedom keeps that resonance too. The system tells you how to read it: push at its own frequency.

**→**

## 10. Cat Qubit Academy · Harshith · 0:15

Everything you just saw is also a course. This is Cat Qubit Academy: eight short levels, from a photon in a box to designing this exact readout. Every level works the same way: you predict, then you play, then you check. Let me show you three of them.

**Click "L1 · A box of light" in the level list.**

---

## D1. Demo: L1 · 0:35

> **Click Play narration.** Say this one line first, then stay quiet while the narration plays (about 20 seconds).

This is the first lesson, read aloud. The voice is ElevenLabs.

> When it finishes, go to L4.

## D2. Demo: L4, the cat appears · 1:05

Level 4 is the cat from Task 1. Before anything runs, you have to commit to a prediction. Starting empty, what will the map look like?

> **Pick "Two blobs plus stripes between them".**

A lot of people pick two blobs with no stripes. That's a 50/50 mixture, and the site is built to catch that mistake.

> **Click Run.**

This runs right in the browser, and it's checked against our research code. Two blobs, with the stripes between them, so it's a real superposition.

> Recommended if time allows (+0:10): set **Photon loss** to **On ×20** and click **Run** again. Say: "Now turn photon loss on. Watch the stripes fade first."

> **Type into Ask Schrö: `why did the fringes fade?`** Then, while it thinks (about 10 seconds), say:

Schrö is our tutor, running on Gemini. It sees which level you're on, what you predicted and your last run, so it answers about your run, not a textbook.

> Read the first sentence of its answer out loud, then go to L8.

### D2+. Talk (optional, +0:20)

> **Only do this if the product thread has confirmed that Talk works on the Vultr site today.** If it hasn't, skip it and don't mention Talk at all.

> Still on L4, **click Talk** and say: "Make the cat bigger and run it again."

Schrö also talks. It's an ElevenLabs voice agent that knows your level and what you got wrong, and it can move the sliders and rerun the simulation for you.

> If nothing happens within 5 seconds, click **End call** and go straight to L8 without comment.

## D3. Demo: L8, design the readout · 1:00

Level 8 is Task 2.4 as a game. Which beats a flat pulse with the same energy budget?

> **Pick "A shaped pulse".** Then **click "Shape near 3.14 MHz"**.

This puts the pulse energy at the ring frequency, the same idea as our best pulse.

> **Click "Fit to budget".**

That rescales the bars so they use exactly as much energy as the square pulse. It's a fair fight.

> **Click ▶ Score.** Then **click Check**.

It beats the square pulse at the same cost. You just found our readout result in about ten seconds, and that's the whole point of the Academy.

> **Switch to Tab 2 (Sponsors).**

---

## 11. Sponsors · Halo · 0:25

Here's how we used each sponsor. Ask Schrö runs on Gemini, the voice is ElevenLabs, and Backboard remembers what each learner tried, so the tutor greets you with a recap. Every simulation run is logged to a Tiger Data time-series table. Vultr hosts this site and its API, and it ran our research sweeps. We built the product in Cursor with Grok. Solana is demo mode only: the credential is signed locally and isn't broadcast.

**→**

## 12. Why, and what's next · Pranav · 0:45

Why build this? Cat qubits are hard to feel from equations alone. The fastest way we found to learn them was to predict, simulate, and be wrong in a specific way. The Academy is that loop, so the next student doesn't need a JAX install to feel why cat qubits work.

Next, three things. First, we put our bit-flip time, phase-flip time and 0.65% readout error into a repetition-code budget, to count how many cats one logical qubit needs. Second, we make the readout self-calibrating: we fit the −23 MHz retune and tune it together with the pulse shape. Third, on the product side, the Academy uses each learner's past mistakes to pick their next hint and level.

Thank you.

---

## If you're running long

Cut these, in this order:

1. The loss-on rerun in L4 (saves 0:10).
2. The second sentence of 2.2 (saves 0:05).
3. The last sentence of 2.4d (saves 0:05).
4. L1 entirely: go straight from the Academy section to L4 (saves 0:35).

If Talk runs, do cuts 1 to 3.

## Words to use, and words to avoid

- **2.6 s is a relaxation time,** 1/Γ_X. Say "the bit-flip time is 2.6 seconds". Don't say "one flip every 2.6 seconds", and don't say "the qubit lasts 2.6 seconds".
- **2 µs in Task 2.4 is the pulse length.** Say "a 2-microsecond pulse". Don't say "the readout takes 2 µs" or "a 2 µs window": the signal is collected through 4.5 µs. The about 2 µs on the 2.2 slide is a different number, the phase-flip time.
- **Solana:** say "demo mode, signed locally, not broadcast". Never say "minted" or "on-chain".
- **Tiger Data:** runs are logged, but there's no chart of them in the site. Don't say "live dashboard".
- **Talk:** don't mention it unless it has been confirmed working (see D2+).
- **Pages to stay away from:** #/inflate, #/errors, #/readout, #/verify.

## Likely judge questions

**"Is 2.6 seconds how often it flips?"**
It's the relaxation time of the bit, 1/Γ_X. In our convention, Γ_X is twice the one-way jump rate, so a single valley actually jumps about every 5 seconds on average.

**"How do you know the eigenvalue really is the bit flip?"**
Parity symmetry splits the Liouvillian into two blocks. The bit flip is the slowest nonzero eigenvalue of its block. We checked it against direct time-domain simulation at four cat sizes, and they agree to about 10⁻⁸.

**"How did you check convergence?"**
We ran a 7 × 7 truncation grid on Vultr, up to 48 × 18 levels. Our 32 × 12 truncation is within 0.035% of the largest. We also tightened the solver tolerance, because the default tolerance left noise at the 10⁻⁴ level.

**"Your readout pulse is 2 µs and the phase-flip time is also about 2 µs. Doesn't the cat phase-flip during readout?"**
Readout asks which valley the cat is in. A phase flip only changes the sign between the valleys, not the valley itself, so it doesn't change the answer. What can spoil the readout is bit flips caused by the drive, and those are what we count.

**"Where do 1.12% and 0.65% come from? Is that a full simulation?"**
They come from the linear-response signal in the buffer, which matches full simulation within 1% (Task 2.3), plus the probability of a bit flip caused by the drive. The pulse is 2 µs long and the output is collected through 4.5 µs. The bit-flip part is a proxy read from the decay of ⟨X⟩, and the caveats are written up in TECHNICAL.md.

**"Why −23 MHz?"**
Pairing needs the pump at ω_p = 2ω_a − ω_b. The pump itself shifts both mode frequencies, so the textbook value misses the resonance. We scanned the pump frequency and found the dip at −23 MHz.

**"Why does the best pulse peak at 3.03 MHz, not 3.14?"**
A 2 µs pulse can only resolve frequency to about 0.5 MHz, and the ring is damped. A 0.1 MHz offset is well inside that resolution, so the optimum is sitting on the ring. The 3.2 and 3.1 MHz figures are the same ring, read off in different ways.

**"What's live in the Academy, and what's precomputed?"**
L1 to L4, and the L8 scoring, run in your browser. The browser simulator is checked against dynamiqs. L5 and L7 read our verified research results, and L6 runs on the Vultr server.

**"How did you use AI?"**
It's disclosed in the README. Claude Code wrote first implementations, Gemini checked physics and plots, the product was built in Cursor with Grok, and one teammate used Codex. We checked every number with convergence tests and independent methods.

**"Is the Solana credential real?"**
It's demo mode. The claim flow runs and signs locally, but nothing is broadcast and nothing is minted. Moving it to devnet is a next step.

**"What would you do with more time?"**
We'd build a repetition-code error budget from our three numbers, make the readout self-calibrating, and add the physics that makes bit-flip suppression saturate in real devices: thermal photons, Kerr and non-RWA terms.
