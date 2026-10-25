# Cat Qubit Academy

**DuQuantum 2026 · Alice & Bob challenge · Standard track · product layer**
Team: Pranav Reddy, Harshit Aggarwal, Halo Kwok, Xuanyu Zhu

Eight short levels take a beginner from a photon in a box to designing a cat-qubit readout. Predict, play, check. The last level is our Task 2.4 result: put the pulse energy at the 3.14 MHz ring and you beat the square pulse.

**Live:** https://66-42-119-3.sslip.io · **Physics submission:** [`main`](https://github.com/pkarakala/duquantum-cat-qubit/tree/main) (write-ups, notebooks 01–09, results)

## What's here

| Path | What |
|---|---|
| `site/` | Vite + TypeScript app: levels, operator blocks, pulse editor, in-browser one-mode solver |
| `server/` | FastAPI: dynamiqs two-mode simulations, tutor, voice, run log, leaderboard |
| `chain/` | Solana devnet service (demo mode) |
| `deploy/` | Docker Compose and Caddy for the Vultr VM |
| `docs/product/` | Level content, API contract, sponsor notes |

## Pages

| Route | What |
|---|---|
| `#/` | The talk: walkthrough slides in order (Task 1, 2.1–2.4d), then the Academy, sponsors, why. ←/→ steps sections |
| `#/learn/L1`…`L8`, `#/sandbox`, `#/challenge` | The Academy, the operator sandbox, the L8 leaderboard |
| `#/research`, `#/inflate`, `#/errors`, `#/readout`, `#/verify` | Tasks 1.0–2.4 with main's write-ups, notebooks, figures and results |

Details and rebuild steps: [`docs/product/SITE_PAGES.md`](docs/product/SITE_PAGES.md).

## Run it

```bash
cd site && npm ci && npm run dev                                       # the site
pip install -r server/requirements.txt
uvicorn server.app.main:app --port 8001                                # the API, from the repo root
```

Set `VITE_API_BASE` to the API origin. Without it, levels use the in-browser solver and saved presets.

## Sponsors

| Sponsor | Job | Status |
|---|---|---|
| Vultr | Hosts the site and API; ran our simulation batches | live |
| Google Gemini | Schrö the tutor, which runs the simulator before it answers | live with a key |
| ElevenLabs | Level narration, and Talk: the Schrö voice agent, which adapts to the learner's level and mistakes | live with a key |
| Tiger Data | Logs every simulation run (Timescale) | live with a key |
| Backboard | Tutor memory across sessions, fed to Schrö | live with a key |
| Solana | Progress credential | demo only, no transactions |
| SpaceX · xAI Grok + Cursor | Built the product layer | dev tools |

## How we used AI

Built with Cursor agents and the Grok bot. Claude Code helped with integration and fixes. The physics and its AI disclosure are on [`main`](https://github.com/pkarakala/duquantum-cat-qubit/tree/main).
