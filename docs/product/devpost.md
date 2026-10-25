# Cat Qubit Academy (product sections for the Devpost)

These sections are for Harshit to merge into the physics Devpost. Placeholders `<ACADEMY_URL>`, `<VIDEO_URL>`, and `<DEVPOST_URL>` are unfilled. This branch has no public URL, no Vultr host, and no Solana transaction.

## Inspiration

We could not find a learner tool for bosonic or cat qubits. What we did find is gate-model teaching (IBM Composer, Quirk, Black Opal, Katas), discrete photons (Quantum Flytrap), or developer notebooks (dynamiqs, QuTiP, Bosonic Qiskit, Alice & Bob's Felis notebooks). The Academy is the missing middle: a short course that ends on the same cat-qubit circuit this repo already simulates.

## What it does

Each of the 8 levels is the same loop: predict, then play, then check, then a short aha. L1 is a box of light, L2 the leaky box, L3 pair loss, L4 the cat, L5 bit flips against phase flips from verified records, L6 an operator-block editor for the two-mode circuit, L7 the readout ring, and L8 a pulse the learner shapes against a square pulse.

Schrö, the tutor, has to run the simulator before it answers. `POST /api/tutor` declares 5 tools: `run_sim`, `get_level_state`, `get_record`, `lookup_grid`, and `check`. The number guard drops a quantity that a tool result, a record, the learner state, or a level constant does not already back. Voice can ask the same question through `POST /api/voice/tts` and the client tools `set_param`, `run_sim`, `show_hint`, `next_level`, and `ask_tutor`. `ask_tutor` is on, and it speaks only that guarded reply.

L1 to L4 and L8 run in the browser solver. L5 reads verified records. L6 posts `POST /api/sim/expr` only when an API base is set, then falls back to a named preset. The engine string on a local one-mode call is dynamiqs 0.3.7. Real Research numbers come only from records. The L8 page has a link toward Real Research, and the Lab routes are not mounted on this branch.

## How we built it

Cursor agent lanes wrote the product from the briefs in [the product briefs](briefs/) and the plan briefs. Grok Bot was the planned walk of the 8 levels. That walk was not run.

What is live when the matching key or URL is set: Gemini (`POST /api/tutor` and the number guard), ElevenLabs (`POST /api/voice/tts` and the 5 client tools), and Timescale (`POST /api/runs`, `GET /api/community/alpha` on the `sim_runs` hypertable and the `alpha_choices_5m` aggregate, plus `GET /api/leaderboard` and `GET /api/progress`). Also live in the page, with no sponsor key: the browser solver, the 8 levels, the block editor, and the tutor guard.

What health labels demo: Vultr, Solana, and Backboard. The dynamiqs routes `POST /api/sim/one_mode`, `POST /api/sim/two_mode`, and `POST /api/sim/expr` run in the API process on this machine. No Vultr host was deployed, so a badge that says Live · Vultr dynamiqs names the intended host, not a machine we stood up. `POST /api/chain/credential` returns demo mode and no transaction signature. `POST /api/memory/event` and `GET /api/memory/recap` use the labeled demo adapter. Docker was not built.

Built with, as far as this branch actually contains them: dynamiqs 0.3.7, JAX, Gemini API, ElevenLabs, Tiger Data (TimescaleDB), Cursor, Vite, and Plotly on the academy plots. Vultr, Solana (Metaplex Core), Backboard, and Grok Bot are in the interfaces and are not live deployments. Blurbs for the 8 MLH categories are in [sponsor_writeups.md](sponsor_writeups.md).

## Challenges

Two-mode physics is not an interactive browser loop, so the common builds are precomputed and every run shows a source badge. The tutor will invent a number if nothing stops it, so the guard runs after the model writes and again after any sentence we append from a tool. The page has to keep teaching when the network is down: the browser solver, presets, scripted hints, and the canned replies. There is still no single-file build, because `site/package.json` is not on this branch.

## Accomplishments

A learner can play all 8 levels, edit the two-mode Hamiltonian as blocks, and get a tutor answer that had to call the sim. The 7 misconceptions M1 through M7 are the wrong predictions the levels name. Gemini, ElevenLabs, and Timescale have live paths. The in-browser learning sims are validated against our dynamiqs records.

Scope, in one place. Solana is devnet only, with no real funds, and this branch sent no transaction. The think-aloud is not recorded, so there is no N. The in-browser learning sims are validated against our dynamiqs records, and Real Research numbers come only from records. Two-mode runs live only at a small fixed truncation, and the common builds are precomputed, with a visible source badge. No PII is collected. Gemini's free tier may use content, which is why we collect none. The integrator status has no Cuts section. Unfinished on this branch: a public URL, a Vultr deploy, a Backboard key, a Grok Bot walk, the think-aloud, a Docker image, and the offline single-file build.

## What we learned

The think-aloud is not recorded, so there is no N and no before/after accuracy. That session was the planned evidence of learning, and it is still pending, which is why this section gives no accuracy. What the build itself showed is narrower: a tutor that can call tools will still write a quantity the tools did not return, and the guard is what makes that visible to a learner.

## What's next

Fill `<ACADEMY_URL>` only after a host exists. A Vultr deploy, a devnet credential that actually broadcasts, a Backboard key, the Grok Bot walk, and the think-aloud are all still open. Publish the DEV draft after the event, within the month. Do not describe today's demo mode as a landed transaction.
