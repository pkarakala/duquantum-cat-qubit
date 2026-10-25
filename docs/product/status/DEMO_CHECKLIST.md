# Demo checklist (2026-10-25, before 12:00 EDT judging)

Tested on integrated @ 69551a1 plus the fixes listed below.
Local stack: API `http://127.0.0.1:8001` (port 8000 is taken by another app on the demo Mac),
site `http://127.0.0.1:5180`, offline fallback `site/dist-single/index.html`.
No secrets are recorded here.

## Results

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | L4 predict → run (cat forms) | PASS | Two blobs + fringes, parity 1.000, in-browser sim badge |
| 2 | L4 tutor "why did the fringes fade?" | PASS | Gemini `gemini-3.5-flash` 200 after fix (was 422 → offline fallback) |
| 3 | L8 shaped pulse beats square | FAIL | "Shape near 3.14 MHz" + Fit to budget + Score still reports "square itself does not win". Do not claim the pass live |
| 4 | L1 predict → run | PASS | |
| 5 | L2, L3, L5 run | PASS | In-browser sim · validated vs dynamiqs, no MOCK |
| 6 | L6, L7 | NOT VERIFIED | Automated pass did not switch levels; not checked by hand |
| 7 | Voice (ElevenLabs) `/api/voice/tts` | PASS | 200 audio/mpeg (~34 KB) after adding `elevenlabs` dep |
| 8 | Tiger run log `/api/runs` | PASS | 200 `{"ok":true}`; browser runs also log |
| 9 | Backboard recap `/api/memory/recap`, `/api/memory/event` | PASS | Recap text returned; tutor greets "Welcome back…" |
| 10 | Solana demo claim | NOT TESTED | Chain service not running locally; health reports solana=demo |
| 11 | Vultr deploy 66.42.119.3 | NOT DONE BY CLAUDE | Bundle + script staged; must be run from Pranav's terminal |

## API endpoints (local)

| Endpoint | Result |
|----------|--------|
| GET /api/health | PASS (gemini, elevenlabs, backboard, tiger true; vultr, solana demo) |
| POST /api/sim/one_mode | PASS (~4 s) |
| POST /api/sim/two_mode | PASS (~2.6 s) |
| POST /api/sim/expr | PASS |
| POST /api/tutor | PASS |
| POST /api/voice/tts | PASS |
| POST /api/runs | PASS |
| GET /api/community/alpha | PASS |
| GET /api/leaderboard | PASS (empty) |
| POST /api/leaderboard | NOT TESTED (needs a verified readout_pulse payload) |
| POST/GET /api/progress | PASS |
| POST /api/memory/event, GET /api/memory/recap | PASS |
| /api/chain/* | NOT TESTED (chain service not running locally) |

## Fixes found during the smoke test

- `site/src/tutor/bridge.ts`: the prediction object was sent where the server expects a string (422).
- `server/requirements.txt`: `elevenlabs` and `psycopg[pool]` were missing (TTS 500, API import crash; would also break the Docker image).
- `.env` built from `.env.example`: empty `SIM_TIMEOUT_*_S=` lines crash `/api/sim/*` with 500. Leave them out or give them numbers.

## Presenter: avoid

- `#/inflate`, `#/errors`, `#/readout`, `#/verify`.
- Claiming L8 "beats the square" live (check 3 failed). Show the bar shaping and the hint instead.
- Solana: say demo mode only.
- Port 8000 on the demo Mac belongs to another app; the Academy API is on 8001.
