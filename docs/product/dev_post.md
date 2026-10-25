# DEV post draft

Title: An AI tutor that has to run the simulation before it can answer

Tags: #mlhacks

TEMPLATE UNVERIFIED. The live page at dev.to/mlh-hackathon, fetched for this lane, says to use the official DEV submission template, to include #mlhacks, and to publish during the current calendar month in Eastern Time. That page does not list the post's section headings. The headings below are the brief's fallback.

Note: publish after the event, by Oct 31 11:59 PM ET (within the month). Harshit publishes. This lane does not. Links stay placeholders until they exist: `<ACADEMY_URL>`, `<VIDEO_URL>`, `<DEVPOST_URL>`.

## What I built

Cat Qubit Academy is a short course from a box of light to a cat qubit. There are 8 levels. Each one asks the learner to predict, then play, then check. Schrö, the tutor, is not allowed to answer a physics question until it has run the simulator.

## Demo

The 60-second path is in [demo_script.md](demo_script.md). You open the cat level, predict, run, and ask why the fringes fade. Then you build the two-mode circuit with blocks and open a credential slot that stays in demo mode. There is no public URL on this branch.

## How it works

`POST /api/tutor` calls Gemini with 5 tools: `run_sim`, `get_level_state`, `get_record`, `lookup_grid`, and `check`. L1 to L4 and L8 run in the browser solver. L5 reads verified records. L6 can post `POST /api/sim/expr` and otherwise shows a precomputed build. The local engine string is dynamiqs 0.3.7. After the model writes, the number guard removes any quantity that a tool, a record, the learner state, or a level constant does not back. Voice uses `POST /api/voice/tts`, and `ask_tutor` is one of 5 client tools so a spoken answer goes through that same guard.

## How we used sponsor tech

Gemini is the tutor, and it is live when the key is set. ElevenLabs is the speech path, and it is live as TTS. No agent session was opened, because no agent id was set. Timescale stores runs on a hypertable and serves the room chart from a continuous aggregate, and it is live when the database URL is set. Vultr, Solana, and Backboard are labeled demo: no host, a credential with no transaction signature, and a memory adapter that says it is demo. The blurbs are in [sponsor_writeups.md](sponsor_writeups.md). Cursor agent lanes wrote the code. Grok Bot did not walk the levels.

## What I learned

The think-aloud is not recorded, so there is no N and no accuracy to report. A model that can call a simulator will still write a number the simulator did not return. The guard is the part a learner can trust. Solana is devnet only, with no real funds, and demo mode is not a broadcast. The in-browser learning sims are validated against our dynamiqs records. Real Research numbers come only from records. Two-mode runs live only at a small fixed truncation, and the common builds are precomputed, with a visible source badge. No PII is collected. Gemini's free tier may use content, which is why we collect none. Unfinished: no public host, no Vultr deploy, no Backboard key, no Grok Bot walk, no think-aloud, and no single-file build. The integrator status has no Cuts section.

## What's next

Ship a real host before filling `<ACADEMY_URL>`. Broadcast a devnet credential only when a signer exists, and keep it off mainnet. Turn memory on only with a Backboard key. Run the think-aloud and publish N with it. Note: publish after the event, by Oct 31 11:59 PM ET (within the month).
