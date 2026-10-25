# Academy demo script

There is no public URL. Do not invent one. `<ACADEMY_URL>` stays a placeholder until Harshit has a host. The seconds below are the presenter's clock, not measured latencies. The voice question is: why did the fringes fade?

The hashes `#/learn/L4`, `#/learn/L6`, and `#/learn/L8` are the ones `site/src/academy/ui/shell.ts` writes. `site/src/main.ts` and `site/src/academy/routes.ts` are not on this branch, and neither are `#/sandbox`, `#/challenge`, or `#/verify`.

## 60-second demo

Open the local academy page at `site/src/academy/dev.html`. Start the API only if you want a live Gemini, ElevenLabs, or Timescale call. Vultr is labeled demo either way.

| Seconds | Click / action | Say | If it fails |
|---|---|---|---|
| 8 | Open the academy dev page. Go to the cat level, hash `#/learn/L4`. | This is the cat. Predict before you run. | If the dev page will not open, say the single-file build is not in this tree. Do not substitute a made-up URL. |
| 12 | Choose two blobs plus stripes, then run. | The stripes are the superposition. The badge names the source. | A worker failure falls through to the in-browser solver before a mock preset. A real solver result is badged in-browser. |
| 15 | Type the voice question, or speak it only if an agent id is configured: why did the fringes fade? | Schrö has to run the sim. The guard keeps only a sourced quantity. | If Gemini or the network fails, the canned reply for that question is used, and otherwise the scripted hint ladder. |
| 13 | Open `#/learn/L6` and run the block editor. | Two-mode stays at a small fixed truncation, or a precomputed build, and the badge says which. | With no API base, the page does not fetch. It shows the named preset. Do not call a local API success a Vultr deploy. |
| 12 | Open `#/learn/L8`, score a shaped pulse against the square, then open the credential slot. | Solana is devnet only, with no real funds. This claim was not broadcast. | The credential answer is demo mode and has no transaction signature. Do not open an explorer link. |

The Seconds column sums to 60.

## 45-second Academy video segment

For l7. The whole physics video is capped elsewhere. This segment is the Academy piece. Narration is the middle column only.

| Seconds | Narration | Screen |
|---|---|---|
| 12 | Cat Qubit Academy is Code.org for quantum: from a box of light to Alice and Bob's cat qubit. You predict before you play, then the level checks you. | `#/learn/L4`, prediction locked until a choice |
| 16 | Schrö has to run the simulator before it can answer. Ask why the fringes fade. The number guard keeps only a quantity that a tool, a record, or the level already returned. | Tutor panel, then the live reply or the canned reply |
| 17 | Eight levels, the block editor, and the browser solver are in the app. Gemini, ElevenLabs, and Timescale are live. Solana, Backboard, and Vultr are labeled demo: no host, and no transaction. | `#/learn/L6` blocks, then the L8 claim slot in demo mode |

The Seconds column sums to 45.

## If the network fails

`npm --prefix site run build` and `npm --prefix site run build:single` cannot run: `site/package.json` is absent, and `site/dist-single/index.html` does not exist. Do not pretend that file is the fallback.

What does work with no API base is the academy dev page. L1 to L4 and L8 use the browser solver and badge an in-browser result, which is validated against our dynamiqs records. L5 uses verified records. L6 and L7 show a preset and a source badge. The tutor answers the canned questions (fringes fading, the overshoot, and the readout ring) from `site/src/tutor/canned.json`, and any other question gets the scripted hint. No PII is collected.

## Pre-demo checklist

- `deploy/warm.sh` is not in this tree. There is no Vultr host to warm. For a live tutor or a Timescale row, start the local API with `python -m uvicorn server.app.main:app` from the worktree. Do not commit `server/.env`.
- Open `site/src/academy/dev.html`. Leave `<ACADEMY_URL>` blank.
- Grant the microphone only when an ElevenLabs agent id is set. Otherwise type the voice question.
- Set zoom to 110%.
- Turn notifications off.
- Confirm the credential slot says demo, and that you will not read out a transaction signature.
