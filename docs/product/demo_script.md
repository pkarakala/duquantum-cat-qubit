# Academy demo script

This file is the 60-second live demo and the 45-second video script. The video was not recorded.

There is no public URL. Do not invent one. The release branch on GitHub is `prod/release`. Run the app locally:

```text
npm --prefix site run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/#/learn`. Lessons are `#/learn/L1` through `#/learn/L8`. The block editor is `#/sandbox`. Research routes are placeholders.

Live sponsors: Gemini, ElevenLabs TTS, Timescale, and Backboard. Demo sponsors: Solana and Vultr. Vultr is not hosting this demo. Solana does not broadcast a transaction.

The seconds below are the presenter's clock, not measured latencies. The voice question is: why did the fringes fade?

The hashes `#/learn`, `#/learn/L4`, `#/learn/L6`, `#/learn/L8`, and `#/sandbox` are registered in `site/src/main.ts` and `site/src/academy/routes.ts`.

## 60-second demo

Start the API only if you want a live Gemini, ElevenLabs TTS, Timescale, or Backboard call. Do not describe a local or stored result as a Vultr deploy.

| Seconds | Click / action | Say | If it fails |
|---|---|---|---|
| 8 | Open `http://127.0.0.1:5173/#/learn/L4`. | This is the cat. Predict before you run. The gate stays locked until you choose. | If the dev server will not open, do not substitute a made-up URL. Say the video was not recorded and read this script. |
| 12 | Choose two blobs plus stripes, then Run. | The stripes are the superposition. Read the badge. In-browser means this browser. MOCK means a stored demo. | A worker failure falls through to the in-browser solver before a mock preset. A real solver result is badged in-browser. |
| 15 | If the tutor panel is up, type or speak: why did the fringes fade? | Schrö has to run the sim. The guard keeps only a sourced quantity. Gemini, ElevenLabs TTS, Timescale, and Backboard are the live paths. | With no API base the tutor panel is absent. Use the Hint button. If Gemini fails, the canned reply or the scripted hint is used. |
| 13 | Open `#/learn/L6` and Run a stored build. | Two-mode stays at a small fixed truncation, or a precomputed build, and the badge says which. Vultr is demo. | With no API base, the page does not fetch. It shows the named preset and badges it MOCK. |
| 12 | Open `#/learn/L8`, score a shaped pulse against the square, then open the credential slot. | Solana is devnet only, with no real funds. This claim was not broadcast. | The credential answer is demo mode and has no transaction signature. Do not open an explorer link. |

The Seconds column sums to 60.

## 45-second Academy video segment

Not recorded. Narration is the middle column only. If it is recorded later, this is the Academy piece.

| Seconds | Narration | Screen |
|---|---|---|
| 12 | Cat Qubit Academy is Code.org for quantum: from a box of light to Alice and Bob's cat qubit. You predict before you play, then the level checks you. | `#/learn/L4`, prediction locked until a choice |
| 16 | Schrö has to run the simulator before it can answer. Ask why the fringes fade. The number guard keeps only a quantity that a tool, a record, or the level already returned. | Tutor panel, then the live reply or the canned reply |
| 17 | Eight levels and the block editor are in the app. Gemini, ElevenLabs speech, Timescale, and Backboard are live. Solana and Vultr stay demo: no host, and no transaction. | `#/learn/L6` stored builds, then the L8 claim slot in demo mode |

The Seconds column sums to 45.

## If the network fails

The dev server does not need the API. L1 to L4 compute in the browser and badge an in-browser result, which is validated against our dynamiqs records. L5 and L7 show a stored snapshot and a MOCK badge when no live record bundle is loaded. L6 shows a named preset and a MOCK badge. L8 scores in the browser when linresp loads, and says MOCK when it does not. With no API base the tutor panel is absent, so the Hint button is the scripted ladder. No PII is collected.

`npm --prefix site run build` writes gitignored `site/dist`. Do not commit it, and do not call that folder a public site.

## Pre-demo checklist

- There is no Vultr host to warm. For a live tutor, Timescale row, or Backboard recap, start the local API with `python -m uvicorn server.app.main:app` from the worktree. Do not commit `server/.env`.
- Leave any public URL blank.
- Grant the microphone only when an ElevenLabs agent id is set. Otherwise type the voice question. TTS is the live ElevenLabs path.
- Set zoom to 110%.
- Turn notifications off.
- Confirm the credential slot says demo, and that you will not read out a transaction signature.
- Say that the video was not recorded if someone asks for the recording. Point them at this file.
