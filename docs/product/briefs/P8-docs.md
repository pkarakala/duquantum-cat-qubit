# Brief `p8-docs`: Academy submission text: Devpost sections, sponsor write-ups, demo script, DEV post, README section (via l7)

> **Paste into a new Cursor agent (worktree mode, base `standard-track`):** "You are product lane `p8-docs`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P8-docs.md`, then execute the brief exactly. Keep `docs/product/status/p8-docs.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target EDT |
|---|---|---|---|---|---|
| `p8-docs` | `prod/p8-docs` from `standard-track` | **P-G3 passed**: `docs/product/status/p7-integrate.md` says `PRODUCT FROZEN`, with the think-aloud table, smoke tables, cuts and the timed 60-second path. Physics lane `l7-docs` is in its final pass (it owns `README.md`, `TECHNICAL.md`, `docs/devpost.md` and `docs/video_script.md`) | fast (Sonnet-class) | 2 h | 7:30 AM → **9:30 AM Sun Oct 25**. README section to l7 by **8:15**; Academy video segment by **8:45** (l7's video script is final at 9:00); Devpost text by 9:30 (Devpost closes 10:45) |

## 1. Goal and why
Write the words that judges and sponsors actually read. Five deliverables:
- **`docs/product/devpost.md`:** Academy sections that Harshit merges into the main Devpost text (l7 writes `docs/devpost.md`). Sections: Inspiration, What it does, How we built it (every sponsor), Challenges, Accomplishments, What we learned (including the think-aloud results), and What's next.
- **`docs/product/sponsor_writeups.md`:** one 2–4 sentence submission blurb for each of the 8 MLH categories. Each names the concrete feature, its endpoint, and why it matters for learners.
- **`docs/product/demo_script.md`:** the 60-second live demo and the 45-second Academy segment for the ≤ 4-minute video. It gives exact clicks, the voice question, and the fallback path if the network fails.
- **`docs/product/dev_post.md`:** the DEV Writing Challenge draft.
- **The README "Cat Qubit Academy" section**, delivered to `l7-docs` through **your status file**. Never edit `README.md`.

**Why:**
- The MLH sponsor prizes are judged on these write-ups.
- DuQuantum judges score understanding, learning and honesty.
- The whole project's story is "every number traceable", and one invented statistic undoes it.

**Number rule (no exceptions).** Every number in these docs comes from exactly one of these sources:
- (a) **a record**: cite its id, and display it exactly as README/TECHNICAL display it;
- (b) **a LEVELS allowed constant**: cite the level;
- (c) **the think-aloud table** in the p7 status file: cite the row and N;
- (d) **a count of repo artifacts or a version pin**: 8 levels, 7 misconceptions, 5 tutor tools, 4 client tools, 8 MLH categories, `dynamiqs 0.3.7`.

Nothing else is allowed. That means no latency figures, user counts, "x% better" or engagement claims, and **never** SPONSORS' season-submission counts (internal strategy). Describe speed in words.

**Honest scope notes** (they must appear in the Devpost sections, the DEV post and the README section):
- Solana is **devnet only**, with no real funds.
- The learning evidence is a **small-N think-aloud** (state N), not a controlled study.
- The in-browser **learning sims are validated against our dynamiqs records** (golden tests). Real Research numbers come **only** from records.
- Two-mode runs live only at a small fixed truncation, and the common builds are precomputed, with a visible source badge.
- No PII is collected. Gemini's free tier may use content, which is why we collect none.
- What was cut (from the p7 status file's **Cuts** section).

## 2. Read first
- **Product docs:**
  - the spec (`docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md`): §1 why, §3 product, §5 sponsor roles, §9 scope;
  - SPONSORS, all of it: the checklist, DEV, and SpaceXSI's raffle rules;
  - CONTRACT §3 endpoint names and §8 tools;
  - LEVELS: the misconception library and the per-level allowed constants;
  - PLAN §2–§3; HUMAN §4.
- **What was actually built:**
  - `docs/product/status/p7-integrate.md`: the P-G3 checklist, smoke tables, cuts, the Grok Bot checklist, the think-aloud table, the offline dry run, and the 60-second path timings;
  - each `p0`–`p6` status file: deviations, DECISION NEEDED outcomes (for example whether `ask_tutor` exists), and the endpoints verified live.
- **l7's side:**
  - `docs/plan/briefs/12-l7-docs.md`: §3 allowlist, §6.10 video (≤ 240 s, target 225 s), §6.11 Devpost.
  - The current `README.md`, `TECHNICAL.md`, `docs/devpost.md` and `docs/video_script.md` on `standard-track`. Use their **displayed values** for any shared number.
- **Ids:** `results/index.json` and `results/records/*.json`.
- **DEV:** the official DEV template from `dev.to/mlh-hackathon`. Verify it live and record its headings in your status.

## 3. Allowlist (touch nothing else)
- **Files you write:** `docs/product/devpost.md`, `docs/product/sponsor_writeups.md`, `docs/product/demo_script.md`, `docs/product/dev_post.md` and `docs/product/status/p8-docs.md`.
- **Never edit** `README.md`, `TECHNICAL.md`, `docs/devpost.md`, `docs/video_script.md`, `slides/**` (all l7's), any other status file, code, `results/**` or `figures/**`.
- **Never publish or submit anything:** Harshit submits Devpost and MLH, and publishes DEV after the event.
- **No keys or tokens** in any file. Public URLs are fine; use the placeholders `<ACADEMY_URL>`, `<VIDEO_URL>` and `<DEVPOST_URL>` until Harshit fills them.

## 4. Interfaces you implement / rely on
**Facts sheet.** Before writing prose, put this in status:
- what works at freeze (P-G3 ticks);
- the cuts;
- N and the before/after think-aloud accuracy, exactly as in p7's table;
- each record you'll cite (`id | displayed value | where README shows it`);
- the live URL;
- whether `ask_tutor` and narration audio shipped.

**Sponsor facts to name** (one category each; the endpoints come from CONTRACT §3):

| Category | Feature | Endpoint(s) / artifact | Why it matters for learners |
|---|---|---|---|
| Gemini | Schrö tutor: function calling into our simulator and records, structured hint output, and a number guard | `POST /api/tutor`; tools `run_sim`, `get_level_state`, `get_record`, `lookup_grid`, `check` | it must run the sim before answering, and invented numbers are stripped |
| ElevenLabs | voice tutor (ElevenAgents) whose client tools drive the sim, plus narrated concept cards | client tools `set_param`, `run_sim`, `show_hint`, `next_level` (+`ask_tutor` if shipped); `POST /api/voice/tts` | hands-free, accessible, and it moves the sliders |
| Vultr | the live dynamiqs engine (CPU, fp64) and the API hub | `POST /api/sim/one_mode`, `/api/sim/two_mode`, `/api/sim/expr` | JAX can't run in the browser; the instance stays warm |
| Tiger Data | the `sim_runs` hypertable, the continuous aggregate `alpha_choices_5m`, and the leaderboard and progress tables | `POST /api/runs`, `GET /api/community/alpha`, `/api/leaderboard`, `/api/progress` | the live "what cat size is the room choosing" chart |
| Solana | a soulbound Metaplex Core credential, plus a Memo anchor of `sha256(results/index.json)` | `POST /api/chain/credential`, `POST /api/chain/anchor`, `GET /api/chain/anchors` | verifiable learning and verifiable science (devnet) |
| Backboard | per-learner memory of misconceptions; "welcome back" recap | `POST /api/memory/event` (`memory:"Auto"`), `GET /api/memory/recap` (`"Readonly"`); core Gemini calls stay direct | the tutor remembers what you got wrong |
| SpaceXSI | built with Cursor agent lanes (paste-ready briefs); Grok Bot QA walked the 8 levels | `docs/product/briefs/`, `docs/plan/briefs/`, the Grok checklist in p7 status | (process) **remind Harshit to tick the raffle opt-in** |
| DEV | the writing challenge post | `docs/product/dev_post.md`, `#mlhacks` | explains the guard idea to other builders |

**Other inputs:**
- **"Built with"**: copy the SPONSORS checklist list.
- **Demo:** P7's timed 60-second path and the routes registered in `site/src/main.ts`.
- **Voice question:** "why did the fringes fade?"
- **Network-fail path:** the single-file build, presets with badges, scripted hints and canned answers.

## 5. Tests to write FIRST (TDD)
This lane owns no test file. Put these checks in status as a checklist **before** writing prose, and run them at each milestone as the one-off commands in §9.
1. **`number_ledger`:** every number in the 4 docs and the README section appears in the status **Number ledger** (`number | file:line | source: record id / LEVELS L# / think-aloud row / artifact count / version`). The residual list printed by the §9 scan must be empty.
2. **`sponsor_shape`:**
   - exactly 8 `## ` sections, in the order of the §4 table;
   - each has 2–4 sentences and contains "learn";
   - the Gemini, ElevenLabs, Vultr, Tiger, Solana and Backboard sections each contain a backticked `/api/` endpoint;
   - SpaceXSI contains "Cursor", "Grok Bot" and the raffle opt-in reminder.
3. **`devpost_sections`:**
   - the 7 headings from §1;
   - the scope notes: "devnet", "think-aloud" with N, and "validated against" dynamiqs records;
   - no "first", "proves" or "guarantees" unless the claim is qualified ("we could not find a learner tool for…").
4. **`demo_timing`:**
   - the 60-second table sums to ≤ 60 s;
   - the Academy video segment is ≤ 45 s, with narration ≤ 105 words (140 wpm);
   - every route named exists in `site/src/main.ts` or `site/src/academy/routes.ts`;
   - a "If the network fails" section exists.
5. **`dev_post_shape`:**
   - the title line, and the `#mlhacks` tag (at most 4 tags);
   - the official template headings (or `TEMPLATE UNVERIFIED` with fallback headings);
   - the note "publish after the event, by Oct 31 11:59 PM ET (within the month)".
6. **`links_and_secrets`:** relative links exist (`Test-Path`), and no `API_KEY`, `sk-` or base58 secret pattern appears.
7. **`allowlist`:** `git diff --name-only standard-track...HEAD` contains only §3 paths.

## 6. Method, step by step
1. **(7:30–7:40) Setup.**
   - Create `prod/p8-docs`, copy the status template, and add the §5 checklist and the facts sheet (§4).
   - If p7's think-aloud is "pending until 7:45", leave N as a placeholder and fill it in at 7:45.
2. **(7:40–8:15) README section.** Write a section of at most 25 lines:
   - what the Academy is (one sentence: "Code.org for quantum: from a box of light to Alice & Bob's cat qubit");
   - the 8 levels, in one line each;
   - how to open it (`<ACADEMY_URL>`, or the offline single file);
   - the tutor-has-to-run-the-sim idea;
   - the sponsor list, one line;
   - the scope notes.

   Put it in status under **For l7-docs**, with a paste prompt for l7: "Insert the block below verbatim as section `## Cat Qubit Academy` after the Lab link; keep every number as written." Ask Harshit to relay it. l7's final pass runs 8:00–10:00.
3. **(8:15–8:45) `demo_script.md`:**
   - the **60-second demo**: a table of `Time | Click / action | Say | If it fails`, built on P7's timed path;
   - the **45-second Academy video segment**: `Time | Narration | Screen`;
   - **If the network fails**: open `site/dist-single/index.html`, where L1–L5 run in the browser, L6–L8 show presets with their badge, and the tutor answers the 3 demo questions from the canned set;
   - a **pre-demo checklist**: run `warm.sh`, open the tabs, grant the mic permission, set zoom to 110%, turn notifications off.

   Put the 45-second segment in status under **For l7-docs (video)** by 8:45.
4. **(8:45–9:05) `sponsor_writeups.md`** from the §4 table. Write concrete, present-tense facts that the p7 smoke or e2e evidence shows working. If a feature was cut, the blurb says what does work.
5. **(9:05–9:25) `devpost.md`:**
   - **Inspiration**: we could not find a learner tool for bosonic or cat qubits (spec §1 lists what exists).
   - **What it does**: the predict → play → check → aha loop, the tutor, and Real Research.
   - **How we built it**: every sponsor, plus Cursor lanes and the Grok Bot QA.
   - **Challenges**: two-mode isn't interactive, so presets and badges; the number guard; offline-first.
   - **Accomplishments.**
   - **What we learned**: the think-aloud table summary, with N.
   - **What's next.**
6. **(9:25–9:30) `dev_post.md` draft.**
   - Title: "An AI tutor that has to run the simulation before it can answer". Use the official template structure and add `#mlhacks`.
   - The story: the problem (LLMs invent physics), the guard and tools, what learners did, honest limits, links.
   - It may be finished after 9:30 because it publishes later, but commit a complete draft by 9:30.
7. Run all §5 checks, fill the ledger, commit with explicit paths, and set `DONE`.

## 7. Outputs
- **The four docs** listed in §3.
- **Status file sections:**
  - the facts sheet;
  - the Number ledger;
  - **For l7-docs** (the README section plus paste prompt) and **For l7-docs (video)** (the 45-second segment);
  - the §5 checklist with results;
  - the DEV template headings, as verified;
  - a **Harshit submission list**: each MLH category → which blurb → the raffle opt-in for SpaceXSI → DEV publish deadline.
- **No records, figures or code.**

## 8. Acceptance gates
1. **Checks:** §5 checks 1–7 all pass, and the number ledger has no residuals.
2. **Write-ups:** all 8 sponsor blurbs exist. Each is 2–4 sentences, names a feature and an endpoint (or artifact), and says why it matters for learners.
3. **Scope notes:** all five appear in `devpost.md`, `dev_post.md` and the README section.
4. **Demo:** the 60-second demo is ≤ 60 s, the video segment is ≤ 45 s and ≤ 105 words, and the fallback path is written.
5. **Hand-offs:** the README section and the video segment are in status for l7, and Harshit was asked to relay them (log the time).
6. **Shared numbers:** every number shared with README, TECHNICAL or the physics Devpost is displayed identically.
7. **Allowlist:** clean. Nothing was published or submitted by the agent.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
git switch -c prod/p8-docs standard-track; Copy-Item docs/plan/status/_TEMPLATE.md docs/product/status/p8-docs.md
git show prod/p7-integrate:docs/product/status/p7-integrate.md | Out-File -Encoding utf8 $env:TEMP\p7-status.md   # if not merged yet
& $env:DUQ_PY -c "import re,sys; [print(f'{p}:{i}: {m}') for p in sys.argv[1:] for i,l in enumerate(open(p,encoding='utf-8'),1) for m in re.findall(r'(?<![A-Za-z_\d.])\d[\d,]*(?:\.\d+)?(?:[eE]-?\d+)?', l)]" docs/product/devpost.md docs/product/sponsor_writeups.md docs/product/demo_script.md docs/product/dev_post.md
(Get-Content docs/product/demo_script.md -Raw) -split '\s+' | Measure-Object | Select-Object Count       # adapt to the 45 s segment only
Select-String -Path docs/product/*.md -Pattern 'API_KEY|sk-[A-Za-z0-9]{16,}'
Select-String -Path site/src/main.ts,site/src/academy/routes.ts -Pattern "#/learn|#/sandbox|#/challenge|#/inflate|#/verify"
git diff --name-only standard-track...HEAD
```
Compare the scan output against the Number ledger. Any number that isn't in the ledger is a residual: fix the text or cite a source.

## 10. Out of scope / do not
- **Don't invent anything:** numbers, quotes, participants, features or sponsor facts. If p7 didn't verify it, don't claim it.
- **Don't overstate:** no "first", "proves" or "guaranteed". No "students learned X%" from a small N. No mainnet wording.
- **Don't copy SPONSORS' internal numbers** (season submission counts, credit amounts) into public text.
- **Don't edit l7's files or README.md.** Don't touch code, records or figures.
- **Don't publish, submit or post** anything, and don't add `notes/` content or any participant's real name. Use "Participant A, B, C" with their consent as recorded by p7.

## 11. If blocked (DECISION NEEDED + fallbacks + cut line)
> **Q:** l7's `docs/video_script.md` caps the whole video at 240 s (target 225 s) with no Academy time, so a 45 s Academy segment makes it run long. **Options:** A) l7 trims physics to about 195 s and the Academy segment goes in at 3:15. B) A separate ≤ 60 s Academy video, linked from the MLH submissions. **Recommendation:** A (one Devpost video). **Blocking?** no: I write the 45 s segment either way.

> **Q:** The think-aloud is not recorded by 8:30. **Options:** A) "What we learned" says the session is pending and gives no numbers. B) Drop the learning claim. **Recommendation:** A. **Blocking?** no.

**Other triggers:**
- **A number has no ledger source:** remove it or replace it with words. Never round a record differently from README.
- **A sponsor feature was cut:** the blurb describes the working fallback honestly. For example, if Solana's credential was cut, describe the anchor.
- **The DEV template can't be reached:** use fallback headings (What I built · Demo · How it works · How we used sponsor tech · What I learned · What's next) and mark it `TEMPLATE UNVERIFIED`.

**Cut order** (if behind at 9:10):
1. DEV post polish (keep a complete draft).
2. Devpost "What's next".
3. Demo pre-demo checklist detail.

**Never cut:** the 8 sponsor blurbs, the demo script with its fallback path, the README section for l7, the scope notes, and the number ledger.

## 12. Hand-off (status contents + 3 questions Harshit should be able to answer — questions only)
**Status at DONE:**
- State, branch and last sha.
- The §5 checklist with results; the Number ledger.
- The facts sheet.
- The For l7-docs blocks, with the relay time.
- The Harshit submission list (category → blurb → link, the SpaceXSI raffle opt-in, DEV publish by Oct 31 ET).
- The DEV template headings as verified.
- Open DECISION NEEDED items, and every claim you dropped and why.

**Explain-back questions** (Harshit answers in `docs/defense.md`; do not write answers):
1. A Gemini judge asks what "grounded" means here. Which tools does the tutor call, which numbers is it allowed to say, and what happens to a number it makes up?
2. Your Devpost cites the think-aloud results. What exactly did you measure, with how many people, and why is that evidence of learning but not proof of it?
3. Why does the Solana anchor make the research results tamper-evident? What does it *not* prove about whether the physics is right, and why is devnet enough for that purpose?
