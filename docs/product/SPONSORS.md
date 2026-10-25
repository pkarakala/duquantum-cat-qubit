# Sponsors: verified facts, integration recipes, prize checklist

Researched Oct 24 2026 from MLH prize pages and vendor docs (sources at the end). "UNVERIFIED" marks claims we could not confirm.

**The official DuQuantum MLH prize list has 8 categories:** SpaceXSI A-Team, ElevenLabs, Gemini, Solana, Tiger Data, Backboard, Vultr and DEV.
- **Commit Fellowship is not on it.** It is a team founder program anyway, so skip it.
- **How to submit:** each category has its own MLH challenge submission at mlh.com/challenges/<id>/submissions/new, **and** a Devpost "built with" entry.
- **Season-wide competition** (submission counts): Gemini 8,378 · ElevenLabs 617 · Vultr 120 · Solana 109 · Tiger 39 · Backboard 10.

## Gemini (prize: swag kits)
- **Models (ai.google.dev):**
  - `gemini-3.8-flash`: stable, **free tier**, and our default.
  - `gemini-4-argon`: flagship, paid.
  - `gemini-3.8-live`: Live API.
  - `gemini-3.8-flash-tts`.
- **Free-tier caveat:** content may be used to improve Google products. We send no PII.
- **SDKs:** `google-genai` (Python), `@google/genai` (JS). **Keys stay on the server** ("never expose keys client-side… run a backend proxy").
- **What we use:**
  - **Function calling** for the tutor tools (`run_sim`, `get_level_state`, `get_record`, `lookup_grid`, `check`).
  - **Structured output** for hint objects `{hint_level, reply, numbers_cited}`.
  - Optional **image input** to "explain this plot", from a PNG snapshot of the current view.
  - The code-execution sandbox has no dynamiqs and a 30 s limit, so we don't use it.
- **Setup:** about 20 min to a first call; 2–3 h for the tutor with tools.
- **Why it's a "best use":** the tutor is *grounded* in our simulator by function calls, and a number guard backs that up. It's an AI that does physics with tools instead of guessing.

## Vultr (prize: M5Stack Tab5)
- **Credits:** register at **discover.vultr.com/mlh**. Put the school as the company and "Student" as the job title. An emailed promo code goes into Billing → Gift Code and gives **$100**. One registration per person.
- **Instance:** **CPU-Optimized**, starting at $0.06/hr for 2 vCPU. Take 4 vCPU or more and 8 GB or more. Provisioning takes seconds.
  - Single-GPU options (A16, A40, L40S) have weak fp64.
  - GH200 has full fp64 but an ARM host (UNVERIFIED wheel risk).
  - Our Hilbert spaces are small and need **fp64**, so CPU is right.
- **Deploy:** docker compose (api + chain + caddy). Caddy gets automatic TLS for `<ip>.sslip.io`, so the GitHub Pages site (HTTPS) can call it without mixed-content errors. About 30–60 min.
- **Why it's a "best use":** the live dynamiqs two-mode engine (JAX can't run in the browser) plus the API hub for every other sponsor.

## ElevenLabs (prize: earbuds)
- **Promo:** a code emailed in event week gives **one free month of Creator** (121k credits, 275 agent minutes). Free tier: 10k credits, 15 agent minutes, non-commercial.
- **ElevenAgents** (formerly Agents):
  - Embeddable widget: `<elevenlabs-convai agent-id="…">`, from `@elevenlabs/convai-widget-embed`. The agent must be public with auth off.
  - Or `@elevenlabs/react` / `@elevenlabs/client` with `Conversation.startSession({clientTools})`.
  - **Client tools** are browser JS functions the agent calls. We expose `set_param`, `run_sim`, `show_hint` and `next_level`, so the **voice tutor drives the simulator**.
  - **Its LLM can be set to Gemini 3.8 Flash** in the agent configuration.
- **TTS:** models `eleven_v4`, `eleven_v4_turbo` and `eleven_flash_v2_5`. Pre-generate the narration mp3s for the 8 concept cards, cache them, and ship them as static files so they work offline.
- **Setup:** 30–60 min for the widget; about 2 h with client tools.

## Tiger Data (prize: Stream Deck Mini)
- **Credits:** **$1,000 for 30 days**, no card needed. Tiger Cloud is Postgres + TimescaleDB, plus vector search and the Tiger CLI/MCP. About 15 min to connect.
- **Use:**
  - A `sim_runs` **hypertable** of every learner experiment.
  - A **continuous aggregate** (`alpha_choices_5m`) feeding a live "what cat size is the room choosing" chart.
  - Leaderboards, progress, tutor_events (schema in CONTRACT §6).
- **Don't use pgai.** The repo was archived May 27 2026.
- **Why it's a "best use":** real time series from many learners, plus a live dashboard backed by a continuous aggregate. That is exactly what MLH's copy highlights.

## Solana (prize: hardware wallets) · core
- **Credential:** a **Metaplex Core soulbound asset** (`@metaplex-foundation/mpl-core` + Umi).
  - Use the `PermanentFreezeDelegate` plugin with authority None, so it is non-transferable.
  - The server holds a devnet keypair, funded from faucet.solana.com, and mints to the learner's Phantom address.
  - **Custodial fallback** when the learner has no wallet: mint to a server-held address and show the explorer link.
- **Provenance anchor:**
  - A **Memo program** transaction containing `sha256(results/index.json)` plus a label. Real Research shows "verified results, anchored on Solana at <time>".
  - It is re-anchored at the physics freeze.
- **Optional:** a Solana Action/Blink "claim certificate" share link.
- **Setup:** 2–4 h. **Framing:** "verifiable learning and verifiable science". It extends our provenance theme, which keeps it from looking bolted on. **Devnet only, no real funds.**

## Backboard.io (prize: Tile pack) · core
- **What it is:** a stateful LLM API offering persistent **memory**, RAG over documents, threads, tool calls, and routing across 17,000+ models (Gemini and Grok included), with bring-your-own-key.
  - Base URL `https://app.backboard.io/api`, header `X-API-Key`, SDK `backboard-sdk` (pip/npm).
  - Messages take `memory: "Auto" | "Readonly"`.
  - Model selection is `llm_provider` + `model_name`.
  - New accounts get $5 for 30 days.
  - The code DUQUANTUM is entered at app.backboard.io/hackathon/signup; what it gives is UNVERIFIED.
- **Use:**
  - **One thread per learner.** Prediction outcomes and misconception IDs are written as messages with `memory: "Auto"`.
  - At level start, `GET /api/memory/recap` asks Backboard (`memory: "Readonly"`; BYOK Gemini if available, else Backboard's default model) for a two-sentence recap of this learner's misconceptions.
  - The recap is fed to the **direct** Gemini tutor.
  - The core tutor's Gemini calls stay direct, so both prize claims are clean.
- **Setup:** 30–60 min.

## SpaceXSI A-Team (prize: Cursor keyboard; **a raffle, not judged**)
To qualify:
1. Use **Cursor as the core coding agent** (we do: all lanes).
2. Integrate **Grok Bot** automation into the workflow. Grok Bot is included with Cursor Pro, and the Cursor Pro free month comes by promo email or from the MLH coach.
3. Describe both in the project description.
4. **Opt in to the "Make it Legendary with SpaceXSI" raffle** when submitting.

- **Our Grok Bot use:** a QA agent that walks the deployed Academy (8 levels) and files issues. Optionally, the `tools/ai_review.py --provider grok` second physics review.
- Grok API (optional): `grok-4.7`, base URL `https://api.x.ai/v1`. The Responses API is preferred.

## DEV Writing Challenge ($100)
- Publish on dev.to **within the current month (ET)** with **#mlhacks**, using the official template.
- Topic: "Teaching cat qubits with an AI tutor that has to run the simulation before it can answer."

## Submission checklist (Harshit, by 10:45 AM)
- [ ] Devpost "Built with": dynamiqs, JAX, Gemini API, ElevenLabs, Vultr, Tiger Data (TimescaleDB), Solana (Metaplex Core), Backboard, Cursor, Grok Bot, Vite, Plotly.
- [ ] One MLH challenge submission per sponsor category, each linking the same Devpost and repo, with a 2–3 sentence sponsor-specific description (drafts in `docs/product/sponsor_writeups.md`, lane P8).
- [ ] SpaceXSI raffle opt-in ticked; Cursor + Grok Bot described.
- [ ] Demo-video segment showing each sponsor feature for 5–10 s.
- [ ] The DEV post after the event.

## Sources
- MLH: https://www.mlh.com/events/duquantum/prizes (via hack.mlh.io/duquantum/prizes) and https://www.mlh.com/partners/{gemini,elevenlabs,tigerdata,solana,backboard,spacexsi,vultr}.
- Gemini: https://ai.google.dev/gemini-api/docs/models · /pricing · /live-api · /code-execution · /api-key.
- ElevenLabs: https://elevenlabs.io/docs/eleven-agents/overview · …/customization/tools/client-tools · …/customization/widget · …/customization/llm · https://elevenlabs.io/pricing.
- Vultr: https://www.vultr.com/pricing/ · https://discover.vultr.com/mlh.
- Tiger Data: https://www.tigerdata.com/pricing · https://www.tigerdata.com/docs/get-started/quickstart/quickstart-5-minutes · https://github.com/timescale/pgai (archived).
- Solana / Metaplex: https://www.metaplex.com/docs/smart-contracts/core/guides/create-soulbound-nft-asset · https://solana.com/docs/tools/actions.
- Backboard: https://backboard.io/hackathon · https://docs.backboard.io/quickstart · https://docs.backboard.io/concepts/memory.
- xAI: https://x.ai/news/introducing-grok-bot · https://docs.x.ai/grok-bot/overview · https://docs.x.ai/developers/models.
- DEV: https://dev.to/mlh-hackathon.
