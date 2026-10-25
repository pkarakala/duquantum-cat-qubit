# Status: lane `p8-docs`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p8-docs` |
| Base | `prod/p7-integrate` at `37d9787` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 01:16 |
| Last update (EDT) | 2026-10-25 01:27 |
| Last commit | recorded by `git log -1` on this branch |

The docs describe the app on this branch. They do not describe a plan, a public URL, a Vultr deploy, or a Solana transaction.

## Facts sheet

What works at this tip (`37d9787`, p7 state `DONE_WITH_CONCERNS`). P-G3 was not passed. This is local wiring, not a product freeze.

| Piece | On this branch |
|---|---|
| Gemini | Live when the Gemini key is set. `POST /api/tutor`. 5 tools: `run_sim`, `get_level_state`, `get_record`, `lookup_grid`, `check`. Number guard is in `server/app/tutor/guard.py`. p7 wired the tutor at `server.app.sim` (label p0), not mock-sim. p7 did not call Gemini again. |
| ElevenLabs | Live when the ElevenLabs key is set. `POST /api/voice/tts`. 5 client tools, including `ask_tutor` (on by default). No agent id, so no ElevenAgents session was opened. No mp3 files are in the tree. |
| Timescale | Live when `TIGER_DATABASE_URL` is set. `sim_runs` hypertable, `alpha_choices_5m` continuous aggregate. `POST /api/runs`, `GET /api/community/alpha`, `GET /api/leaderboard`, `GET /api/progress`. p7 also got `{ok: true}` from the in-process sink with no URL. |
| Browser solver | Live. L1–L4 and L8 call the in-browser Crank–Nicolson solver. A real result is badged in-browser, not MOCK. |
| 8 levels | Live. L1 through L8 in `site/src/academy/levels/`. |
| Block editor | Live. Run posts an ExprTree to `POST /api/sim/expr` when an API base is set. |
| Tutor guard | Live. A quantity stays only when a tool, a record, the learner state, or a level constant backs it. |
| Solana | Labeled demo. `POST /api/chain/credential` returns `demo_mode: true`, `tx_sig: null`, `asset_address: null`. No transaction was sent. Devnet only, no real funds. |
| Backboard | Labeled demo. `POST /api/memory/event` returns `source: demo-adapter`, `demo_mode: true`. |
| Vultr | Labeled demo. No host. Dynamiqs runs in the local API process (`dynamiqs 0.3.7` on p7's in-process L1 call). The UI string `Live · Vultr dynamiqs` is the badge for a successful API response, not a Vultr machine. |
| Public URL | None. `<ACADEMY_URL>` is unfilled. |
| `ask_tutor` | Shipped. On unless the mount sets `askTutor: false`. |
| Narration audio | Not shipped as files. The TTS route exists. Concept cards fall back to text when the file is missing. |
| Think-aloud | Not done. No table, no N, no before/after accuracy. |
| Grok Bot | Not done. Cursor lanes did build the briefs. |
| Docker | Not installed. Image not built. |
| Single-file build | Not produced. See the build record below. |
| Cuts | p7 has no Cuts section. Unfinished items are the rows above, not a decision to drop a working feature. |

Live URL: none.

Records cited in the public docs: none. Shared physics numbers were left out so this lane would not redisplay a record. The only version pin in the public docs is `dynamiqs 0.3.7`, which TECHNICAL.md already displays as `dynamiqs 0.3.7`.

## §5 checklist (applied to the finished draft)

- [x] `number_ledger` — scan of the 4 docs is copied under Number ledger. Residuals: none after the ledger rows below.
- [x] `sponsor_shape` — 8 `##` sections in brief order. Each is 2–4 sentences and contains "learn". Gemini, ElevenLabs, Vultr, Tiger Data, Solana, and Backboard each contain a backticked `/api/` endpoint. SpaceXSI contains Cursor, Grok Bot, and the raffle opt-in reminder.
- [x] `devpost_sections` — the 7 headings are present. Scope notes include devnet, think-aloud with N stated as not recorded, and "validated against" dynamiqs records. No "first", "proves", or "guarantees".
- [ ] `demo_timing` — the 60-second column sums to 60. The video column sums to 45. Narration is 91 words (cap 105). "If the network fails" exists. The route-file half fails: `site/src/main.ts` and `site/src/academy/routes.ts` are not on this branch. The hashes the demo names are written by `site/src/academy/ui/shell.ts`.
- [x] `dev_post_shape` — title line, one tag `#mlhacks`, `TEMPLATE UNVERIFIED` plus the fallback headings, and the exact publish note.
- [x] `links_and_secrets` — relative links in the 4 docs resolve. The 4 new docs and this status contain no key variable name, no secret-key prefix, and no base58 secret. `CONTRACT.md` and `HUMAN.md` already name env vars; this lane did not edit them.
- [ ] `allowlist` — files added by this lane are the 5 brief paths. `git diff --name-only standard-track...HEAD` also lists the inherited p0–p7 tree, because this branch was created from `prod/p7-integrate` at `37d9787`, as the task required. See Allowlist.

## For l7-docs

Relay asked at 2026-10-25 01:27 EDT. Harshit: paste this to the l7 lane.

Paste prompt: Insert the block below verbatim as section `## Cat Qubit Academy` after the Lab link; keep every number as written.

```
## Cat Qubit Academy

Code.org for quantum: from a box of light to Alice & Bob's cat qubit.

8 levels, each predict, then play, then check:
- L1 A box of light: a coherent state in one resonator.
- L2 The leaky box: single-photon loss shrinks the blob.
- L3 Two at a time: pair loss freezes parity.
- L4 The cat appears: two valleys, and fringes between them.
- L5 Flip vs flip: bit flips and phase flips, from verified records.
- L6 Build the machine: operator blocks for the two-mode circuit.
- L7 Read the cat: the buffer rings, then settles.
- L8 Design challenge: shape a readout pulse and compare it with the square.

There is no public URL yet. Until Harshit fills `<ACADEMY_URL>`, open `site/src/academy/dev.html`. The offline single-file `site/dist-single/index.html` is not in this tree, because `site/package.json` is absent.

Schrö has to run the simulator before it answers. `POST /api/tutor` uses `run_sim`, `get_level_state`, `get_record`, `lookup_grid`, and `check`. The number guard drops a quantity that a tool, a record, the learner state, or a level constant does not back.

Live: Gemini, ElevenLabs, Timescale, the browser solver, the 8 levels, the block editor, and the tutor guard. Labeled demo: Solana, Backboard, and Vultr.

Solana is devnet only, with no real funds, and no transaction was sent. The think-aloud is not recorded, so there is no N. In-browser learning sims are validated against our dynamiqs records. Real Research numbers come only from records. Two-mode runs live only at a small fixed truncation, and the common builds are precomputed, with a visible source badge. No PII is collected. Gemini's free tier may use content, which is why we collect none. Unfinished here, and the integrator status has no Cuts section: no public host, no Vultr deploy, no Backboard key, no Grok Bot walk, no think-aloud, and no single-file build.
```

The block is 21 lines.

## For l7-docs (video)

Same relay time. l7's script caps the whole video at 240 s (target 225 s) and has no Academy slot. Recommendation stays A: trim the physics narration and place this 45 s segment at about 3:15. A separate Academy video is the other option. Not blocking. Narration below is 91 words.

| Seconds | Narration | Screen |
|---|---|---|
| 12 | Cat Qubit Academy is Code.org for quantum: from a box of light to Alice and Bob's cat qubit. You predict before you play, then the level checks you. | `#/learn/L4`, prediction locked until a choice |
| 16 | Schrö has to run the simulator before it can answer. Ask why the fringes fade. The number guard keeps only a quantity that a tool, a record, or the level already returned. | Tutor panel, then the live reply or the canned reply |
| 17 | Eight levels, the block editor, and the browser solver are in the app. Gemini, ElevenLabs, and Timescale are live. Solana, Backboard, and Vultr are labeled demo: no host, and no transaction. | `#/learn/L6` blocks, then the L8 claim slot in demo mode |

The Seconds column sums to 45. These seconds are a presenter clock, not measured latencies.

## DEV template headings, as verified

Fetched `https://dev.to/mlh-hackathon` during this lane. The page headings that came back are about the program, not the post body:

- How it works
- Build at an MLH hackathon
- Tell the story on DEV
- Help people discover it
- Give your project another chance to shine
- Your network can help your project stand out

The page says to use the official DEV submission template, to include `#mlhacks`, and to publish during the current calendar month (Eastern Time). It does not list the post's section headings. Mark: `TEMPLATE UNVERIFIED`.

Fallback headings used in `docs/product/dev_post.md`: What I built · Demo · How it works · How we used sponsor tech · What I learned · What's next.

## Harshit submission list

Do not submit from this lane. No public URL yet, so every link below stays a placeholder.

| Category | Blurb | Link to attach |
|---|---|---|
| Gemini | `docs/product/sponsor_writeups.md` § Gemini | `<DEVPOST_URL>` and the repo, once public |
| ElevenLabs | same file § ElevenLabs | same |
| Vultr | same file § Vultr. Say demo. Do not claim a host. | same |
| Tiger Data | same file § Tiger Data | same |
| Solana | same file § Solana. Devnet only. Do not paste a signature. | same |
| Backboard | same file § Backboard. Say demo adapter. | same |
| SpaceXSI | same file § SpaceXSI. Tick the raffle opt-in. Describe Cursor. Do not claim the Grok Bot walk happened. | same |
| DEV | `docs/product/dev_post.md` | publish after the event, by Oct 31 11:59 PM ET (within the month) |

Devpost "Built with" should follow the blurbs: name Gemini, ElevenLabs, and Timescale as live, and name Vultr, Solana, and Backboard as labeled demo.

## Single-file build

```text
npm --prefix site run build
npm error enoent Could not read package.json: .../site/package.json
EXIT 254

npm --prefix site run build:single
npm error enoent Could not read package.json: .../site/package.json
EXIT 254

site/src/blocks/package.json has no scripts.
site/dist-single/ does not exist.
```

`site/package.json` belongs to the lab lane and was not merged onto this branch. The lane is not failed for that, or for Docker, or for Vultr.

## Number ledger

Scanner token, then file:line, then source. The scanner reads `dynamiqs 0.3.7` as `0.3`. The displayed version is `dynamiqs 0.3.7`, matching TECHNICAL.md.

| Number | file:line | Source |
|---|---|---|
| 8 | devpost.md:11 | artifact count: 8 levels (LEVELS L1–L8) |
| 5 | devpost.md:13 | artifact count: 5 tutor tools in `server/app/tutor/tools.py` |
| 0.3 | devpost.md:15 | version pin `dynamiqs 0.3.7` (TECHNICAL.md displays `dynamiqs 0.3.7`) |
| 8 | devpost.md:19 | artifact count: 8 levels |
| 5 | devpost.md:21 | artifact count: 5 client tools in `site/src/tutor/tools.ts` (`ask_tutor` shipped) |
| 8 | devpost.md:21 | artifact count: 8 levels |
| 0.3 | devpost.md:25 | version pin `dynamiqs 0.3.7` |
| 8 | devpost.md:25 | artifact count: 8 MLH categories (SPONSORS) |
| 8 | devpost.md:33 | artifact count: 8 levels |
| 7 | devpost.md:33 | artifact count: 7 misconceptions M1–M7 in LEVELS.md |
| 31 | sponsor_writeups.md:35 | brief §5 deadline phrase, day |
| 11 | sponsor_writeups.md:35 | brief §5 deadline phrase, hour |
| 59 | sponsor_writeups.md:35 | brief §5 deadline phrase, minute |
| 60 | demo_script.md:7 | brief §6 presenter cap, 60 s demo. Not a measured latency. |
| 8 | demo_script.md:13 | presenter clock inside that 60 s cap |
| 12 | demo_script.md:14 | presenter clock inside that 60 s cap |
| 15 | demo_script.md:15 | presenter clock inside that 60 s cap |
| 13 | demo_script.md:16 | presenter clock inside that 60 s cap |
| 12 | demo_script.md:17 | presenter clock inside that 60 s cap |
| 60 | demo_script.md:19 | sum of that presenter clock |
| 45 | demo_script.md:21 | brief §6 presenter cap, 45 s segment. Not a measured latency. |
| 12 | demo_script.md:27 | presenter clock inside that 45 s cap |
| 16 | demo_script.md:28 | presenter clock inside that 45 s cap |
| 17 | demo_script.md:29 | presenter clock inside that 45 s cap |
| 45 | demo_script.md:31 | sum of that presenter clock |
| 110 | demo_script.md:44 | brief §6 pre-demo zoom instruction. Not a measurement. |
| 31 | dev_post.md:9 | brief §5 deadline phrase, day |
| 11 | dev_post.md:9 | brief §5 deadline phrase, hour |
| 59 | dev_post.md:9 | brief §5 deadline phrase, minute |
| 8 | dev_post.md:13 | artifact count: 8 levels |
| 60 | dev_post.md:17 | brief §6 presenter cap, the 60 s demo |
| 5 | dev_post.md:21 | artifact count: 5 tutor tools |
| 0.3 | dev_post.md:21 | version pin `dynamiqs 0.3.7` |
| 5 | dev_post.md:21 | artifact count: 5 client tools |
| 31 | dev_post.md:33 | brief §5 deadline phrase, day |
| 11 | dev_post.md:33 | brief §5 deadline phrase, hour |
| 59 | dev_post.md:33 | brief §5 deadline phrase, minute |
| 8 | p8-docs.md:65 | artifact count: 8 levels (README block for l7) |
| 8 | p8-docs.md:79 | artifact count: 8 levels (README block for l7) |

Residuals against the 4-doc scan: none. The README block is not in those 4 files. Its two 8s are the last two rows.

## Allowlist

This lane writes only:

- `docs/product/devpost.md`
- `docs/product/sponsor_writeups.md`
- `docs/product/demo_script.md`
- `docs/product/dev_post.md`
- `docs/product/status/p8-docs.md`

`git diff --name-only 37d9787...HEAD` is the lane diff and must match that list. `git diff --name-only standard-track...HEAD` includes the inherited product tree. Nothing was published or submitted.

## Claims dropped, and why

- No public URL, no sslip.io host, no Pages URL.
- No Vultr deploy and no warm latency.
- No Solana signature, explorer link, or devnet balance. The p6 offline-demo signature was not copied.
- No think-aloud accuracy and no invented N.
- No Grok Bot QA result.
- No narration mp3 claim. The files are not in the tree.
- No latency, test-count, byte-size, or season-submission figure.
- No mock-sim parity from the p4 live turn.
- No record value. README and TECHNICAL were not rewritten, and no shared physics number was redisplayed except the version pin `dynamiqs 0.3.7`.

## DECISION NEEDED

> **Q:** l7's video script has no Academy slot, and a 45 s segment makes a 240 s cut run long.
> **Options:** A) l7 trims physics and inserts this segment. B) A separate Academy video for the MLH forms.
> **Recommendation:** A.
> **Blocking?** no. The segment is in this file either way.

> **Q:** The think-aloud was not recorded.
> **Options:** A) "What we learned" says the session is pending and gives no numbers. B) Drop the learning claim.
> **Recommendation:** A. That is what the docs say.
> **Blocking?** no.

## Explain-back for Harshit (questions only)

1. A Gemini judge asks what "grounded" means here. Which tools does the tutor call, which numbers is it allowed to say, and what happens to a number it makes up?
2. Your Devpost cites the think-aloud results. What exactly did you measure, with how many people, and why is that evidence of learning but not proof of it?
3. Why does the Solana anchor make the research results tamper-evident? What does it *not* prove about whether the physics is right, and why is devnet enough for that purpose?

## Deviations from the brief

- The branch was created from `prod/p7-integrate` at `37d9787`, not from `standard-track`. p7 is `DONE_WITH_CONCERNS`, not `PRODUCT FROZEN`.
- The checklist and facts sheet were written into this status with the draft, not as an earlier commit.
- `TEMPLATE UNVERIFIED` because the live DEV page does not list post headings.
- Demo routes are the hashes the shell actually sets. Sandbox, challenge, and verify are not registered here.

## Notes for Claude's later review

- Do not upgrade Vultr, Solana, or Backboard from demo when quoting these pages.
- Do not fill `<ACADEMY_URL>` until a host exists.
- The presenter seconds are a clock for the person at the keyboard. They are not API timings.
