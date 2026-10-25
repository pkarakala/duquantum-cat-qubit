# Brief `p7-integrate`: Product integrator: wiring, Vultr deploy, end-to-end QA, offline dry run, freeze

> **Paste into a new Cursor agent (worktree mode, base `standard-track`):** "You are product lane `p7-integrate`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P7-integrate.md`, then execute the brief exactly. Keep `docs/product/status/p7-integrate.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target EDT |
|---|---|---|---|---|---|
| `p7-integrate` | `prod/p7-integrate` from `standard-track` (the product integration branch; it never writes `standard-track` itself, see §6.2) | every product lane reviewed (P0–P6), **plus physics `l6-lab` merged** on `standard-track` (until then l6 owns `site/package.json`, `main.ts`, `index.html` and the vite configs) | strongest (Opus-class): merge judgement and end-to-end debugging | 3 h | 4:30 AM → **7:30 AM Sun Oct 25 (product freeze, P-G3)** |

## 1. Goal and why
You turn the reviewed product lanes into **one working Academy**: a public site, a warm Vultr API, and an offline single-file build.
- **You own the site entry points.** After l6 merges, you are the **only** editor of `site/package.json`, `site/src/main.ts`, `site/index.html` and `site/vite*.config.ts` (CONTRACT §0).
- **The routes you register:** `#/learn` and `#/learn/L1` to `#/learn/L8`; `#/sandbox` and `#/challenge`; the Lab pages, grouped under a "Real Research" nav group; `#/about`.
- **The rest of the job:** apply the npm deps each lane requested; copy the generated presets and audio; prepare the deploy and keep-warm commands, and verify end to end; run the Grok Bot QA pass, the network-off dry run and the think-aloud tests; freeze at 7:30 AM against the P-G3 checklist.

**Why it matters:**
- **Judges see one URL**, and the 60-second demo must survive a dead network.
- **Two-mode dynamiqs is not interactive** (CONTRACT §3: 5.5–76 s per run). So the precomputed presets must cover the L6 common builds and the L7 signals, the Vultr instance must stay warm, and the fallback badge must show the truth.
- **The SpaceXSI raffle needs real Grok Bot use** in the workflow.

**Timing reality:**
- Harshit sleeps 2:30–6:00 AM (HUMAN §5) and runs every SSH step himself, so the server redeploy happens **6:00–6:25**. Until then, test against a local `uvicorn`.
- P8 writes `demo_script.md` only after the freeze. You dry-run the 60-second path in §6, and P8 formalizes it.

## 2. Read first
- `AGENTS.md`.
- **CONTRACT:** §0–§1 (ownership; **only you** edit the site entry files); §2 (env); §3 (API, CORS, and the **"two-mode is not interactive"** paragraph: live shape 16×5, 15 s two-mode and 8 s one-mode timeouts, precomputed builds, the client fallback order, and keeping the instance warm); §5 (the TS solver runs in a Web Worker); §7 (`LevelSpec.preset`).
- **PLAN:** §2 (gates P-G2 and P-G3), §3 (cut order and never-cut list), §4 (verification).
- **HUMAN:** §2 (Vultr deploy), §3 (think-aloud), §5 (sleep block).
- **SPONSORS:** SpaceXSI (raffle rules) and the submission checklist.
- **Physics briefs:** `docs/plan/briefs/90-integrator.md`: §6.1 (merge protocol), §6.6 (push requests) and §11 (wording); `docs/plan/briefs/91-reviewer.md` (verdict file and format); `docs/plan/briefs/11-l6-lab.md`: §4 (npm scripts, `renderRoute(hash, root, b)`, vite configs, banner) and §8 (`dist-single` must contain only `index.html` and stay < 15 MB; the `file://` check with no http(s) requests).
- **Every product status file** `docs/product/status/p0…p6-*.md`, especially each one's **For P7** section (deps, routes and mount functions, env vars, copy jobs, open DECISION NEEDED). Also `deploy/README.md` from P0.

## 3. Allowlist (touch nothing else)
- **Site entry files:** `site/package.json`; `site/package-lock.json` (it must change with the deps; CONTRACT §1 doesn't list it, so say so); `site/src/main.ts`; `site/index.html` (including a small `<style>` block for the nav groups); `site/vite.config.ts` and `site/vite.single.config.ts`.
- **Routes:** `site/src/academy/routes.ts`, plus your integration tests in `site/src/academy/routes.test.ts` (CONTRACT gives you no test path; note that).
- **Generated copies only.** Never hand-edit these, and log a sha256 for each file: `site/src/academy/presets/*.json` (P2 copies them per the P0 and P2 briefs; you re-copy from `server/precomputed/presets/` only if P0 re-ran `precompute.py` after P2 merged, and tell P2 in your status); `site/public/audio/*.mp3` plus `manifest.json`, copied from `server/precomputed/audio/`.
- **Deploy:** the runbook sections of `deploy/README.md`, plus new files `deploy/smoke.ps1` and `deploy/warm.sh`. Compose services and the `Caddyfile` stay P0's; changes to them need a DECISION NEEDED.
- **Your records:** `docs/product/status/p7-integrate.md`, `docs/product/status/p7-shots/**`, and merge commits on `prod/p7-integrate`.
- **Never:** another lane's source (send it back instead), or l6's tests; `site/src/data/live/**`, `src/`, `results/`, `figures/`, `server/app/**`; CONTRACT or LEVELS; any `.env` with real values, or `notes/`. **Never push** without Harshit's OK.

## 4. Interfaces you implement / rely on
**Boot and routing (`main.ts` + `routes.ts`):**
- `export function boot(win = window)` sets `location.hash = '#/learn'` when the hash is empty.
- It then dispatches: `academyRoute(hash)` from `routes.ts` returns a renderer or `null`. On `null`, it falls through to l6's `renderRoute(hash, root, loadBundle())`. That keeps l6's default-to-Inflate behaviour, so l6's router tests still pass.
- Use the mount names each lane gives under **For P7**.

| Hash | Renders |
|---|---|
| `#/learn` | P2 progress map |
| `#/learn/L1` … `#/learn/L8` | the P2 level page, plus P4 `mountTutor(root, bridge, {apiBase})`; on L8 also P6's claim UI |
| `#/sandbox` | P3 blocks and the P2 sandbox |
| `#/challenge` | P5 leaderboard view |
| `#/inflate`, `#/errors`, `#/readout`, `#/verify` | l6 Lab pages, plus P6's anchor list (`GET /api/chain/anchors`) under "Real Research" |
| `#/about` | l6's About page |

- **Nav** (`index.html`): three groups, **Academy** (Learn, Sandbox, Challenge), **Real Research** (Inflate, Error budget, Readout designer, Verification) and **About**. Set `aria-current="page"` on the active link. The nav wraps at 375 px.
- **Build env:** `VITE_API_BASE`: the Vultr `https://<ip-dashes>.sslip.io` (in dev, `http://localhost:8000`); `VITE_ELEVENLABS_AGENT_ID`, from P4. Anything `VITE_*` ships to the browser, so **never put a secret there**.
- **Vite configs:** Keep l6's `base './'` and output directories. The single-file build must **inline P1's Web Worker** (for example a `?worker&inline` import, or `worker.format: 'es'`). Verify that it runs from `file://`. If `site/public/audio` would put files beside `dist-single/index.html` (l6 gate: only `index.html`), set `publicDir: false` in `vite.single.config.ts`. Offline concept cards then show text only, which is cut item 3 anyway.
- **Preset coverage:** every `LevelSpec.preset` id, L1 to L8; L6: P0's four builds `correct`, `missing_kappa_b`, `eps_z_drive_wrong` and `a_bd2_wrong`, plus the 32×12 and 24×6 references; L7: ⟨b⟩± for **every** ε_Z/g₂ ∈ {0.05, 0.1, 0.2, 0.5, 1, 2, 3}, both wells; each preset carries its source metadata (Na×Nb, params hash).
- **Fallback badge** (CONTRACT §3): server (3 s; L6 waits up to 15 s with a progress indicator), then the nearest preset, then the in-browser one-mode solver. The badge names whichever source is active.
- **Deploy** (P0's `deploy/docker-compose.yml` and `Caddyfile`): Host: `<ip-with-dashes>.sslip.io`, with automatic TLS from Caddy. `/opt/academy/.env` (api only, with **no** `SOLANA_SECRET_KEY_B58`) sets `API_HOST=<ip-with-dashes>.sslip.io` and `ALLOWED_ORIGINS=https://pkarakala.github.io,http://localhost:5173,http://localhost:4173,null` (`null` is for the `file://` build). The chain secret lives only in `/opt/academy/chain.env` (CONTRACT §2 secret isolation). Deploy with `docker compose --env-file /opt/academy/.env up -d --build` from `deploy/`.
- **Keep warm:** Run one always-on instance, and never stop it from 6:00 to 11:30 AM. Compose uses `restart: unless-stopped`, and the JAX compile cache lives on a volume (both P0's). A cron job `*/5` curls `/api/health`. `deploy/warm.sh` makes one one-mode call, two 16×5 two-mode calls and one tutor call. Run it before each demo window.
- **Merge preconditions:** The reviewer verdict `PASS` or `PASS_WITH_NOTES` is in `docs/plan/status/reviews/<slug>.md` on `review/<slug>-r<N>`, at the lane's **current** sha (the 91-reviewer convention; PLAN §5). The lane's status says `DONE`.

## 5. Tests to write FIRST (TDD)
Write these first and watch them fail. Commit `[p7-integrate] tests first`.
1. **Routes** (`routes.test.ts`, jsdom; mock Plotly, `fetch` and `Worker`): every hash in the §4 table renders without throwing, and shows its `h1`; an empty hash at boot goes to `#/learn`; `#/nope` falls through to l6's default; the nav has the 3 groups, with the 4 Real Research links; every `input`, `select` and `button` has an accessible name.
2. **Preset coverage** (same file): each `LevelSpec.preset` resolves and parses; all 4 L6 builds are present; L7 covers every ε_Z grid value × valley. Log the total preset bytes. The single-file build must stay < 15 MB.
3. **Fallback order** (same file, fake timers): L6 with `fetch` rejecting shows the `preset` badge; L6 with `fetch` hanging for more than 15 s shows the progress indicator, then `preset`; L4 with `fetch` rejecting and no preset shows `in-browser one-mode`; a good response shows `server`. If P2 exposes no hook for the badge, raise a DECISION NEEDED (§11).
4. **`deploy/smoke.ps1 -Base <url>`** (write it before deploying, then run it against local uvicorn). It prints `check | status | wall_ms` and exits 1 on any required failure. `feature_disabled` counts as SKIP when a key is absent. It calls: `GET /api/health` (feature flags); `POST /api/sim/one_mode`; `POST /api/sim/two_mode` at **16×5, twice** (the second must return `meta.cached == true`); `POST /api/sim/expr` with the L6 correct build; `POST /api/tutor` with the L4 question (`tool_calls ≥ 1`, `guard.passed`); `GET /api/memory/recap`; `POST /api/voice/tts`, twice (cache); `GET /api/community/alpha`, `GET /api/leaderboard` and `GET /api/chain/anchors`.
5. **Artifact checks:** `npm run build` and `npm run build:single` exit 0; `site/dist-single/` holds only `index.html`, < 15 MB; no `API_KEY`, `sk-` or base58 secret pattern anywhere in `dist*` or `dist-single`.

## 6. Method, step by step
**6.1 (4:30–4:45) Intake.** Create `prod/p7-integrate` and the status file. Build the lanes table (`lane | state | verdict | reviewed sha | For P7 asks | open DECISION NEEDED`) and copy the P-G3 checklist (§8) into status. A lane still unreviewed at 5:15 AM is cut per PLAN §3; log it.

**6.2 (4:45–5:25) Merge, per the 90-integrator §6.1 discipline.**
1. **P1 allowlist:** `git diff --name-only standard-track...prod/<slug>` must be a subset of the lane's CONTRACT §1 row plus its status file.
2. **Preconditions:** see §4 (verdict at the current sha, status `DONE`).
3. Run `git merge --no-ff prod/<slug> -m "[p7-integrate] merge <slug>"`. Conflicts outside `site/src/academy/presets/**` or your own files: run `git merge --abort` and send the lane back (add a **Sent back** row to your status).
4. After each merge, run the server and site suites. If either goes red, run `git revert -m 1 --no-edit HEAD` and send the lane back.
5. **Order:** p1, p3, p0, p2, p5, p6, p4.
6. **Physics first.** Never ask for review or merge time while a physics gate needs it.
7. **Who writes `standard-track`.** You never write `standard-track` yourself: the main checkout has it checked out, and the physics integrator is its only writer. Instead, write `MERGE REQUESTED: prod/p7-integrate at <sha>` in your status and ask Harshit. The integrator then merges it between physics merges.

**6.3 (5:00–5:30) Wire.** Deps via `npm --prefix site install --save-exact` for each requested dependency (`blockly`, `@elevenlabs/client` or `@elevenlabs/convai-widget-embed`, any P6 wallet dep, and `vitest`/`jsdom` if missing); record the resolved versions. Then the routes, nav, boot, env and vite configs. Copy the presets and audio and log their sha256 values. Get tests 1–3 green, then commit.

**6.4 (5:30–6:00) Local end to end.** Start `uvicorn` and `npm run dev`, then run `smoke.ps1 -Base http://localhost:8000`. Walk all 8 levels at desktop (≥ 1280 px) and at 375 px, saving `p7-shots/<route>-{desktop,375}-local.png`. **By 5:50**, put the exact **Harshit deploy block** (§9) in status, with the sha to deploy.

**6.5 (6:00–6:25) Deploy (Harshit runs SSH).** Run `smoke.ps1 -Base https://<host>`, install the cron job and run `warm.sh`. Record the warm 16×5 wall time (must be < 15 s) and the cached repeat. If the cold start is over 60 s, warm again and note it.

**6.6 (6:25–6:50) Public end to end.** Use Pages if the repo is public, else `npm run preview` with `VITE_API_BASE` pointing at the host. Check:
- all 8 levels at desktop and 375 px (`-public.png` shots);
- a grounded tutor answer, with the `run_sim` chip and ✓;
- voice moves a slider;
- a run is logged to Tiger and appears in the community chart within 5 min;
- a credential is minted (custodial is fine), with its explorer link;
- the anchor tx is visible in Real Research.

**6.7 (from 6:30) Grok Bot QA.** Harshit enables Grok Bot in Cursor Pro, and you paste this prompt from status: "Open `<URL>`. For L1–L8: predict, run, check, and ask the tutor one question. File every bug as `- [ ] L<n> · severity · steps · expected · actual`."
- If Grok Bot cannot browse, run it over `site/src/academy/levels/*.ts` vs `LEVELS.md` and the `p7-shots`, and **say which you did** (the raffle needs honest use).
- Triage each issue: `fix-by-send-back <lane>`, `fixed in P7 wiring <sha>`, or `won't fix (why)`.

**6.8 (6:50–7:20) Think-aloud** (HUMAN §3; Harshit runs it).
- You prepare and fill the table, and keep time: `participant | background | L2/L3/L4 prediction (✓/✗, M-id) | stuck at | quote | L3 re-ask | L4 re-ask`.
- HUMAN §3 says 7:00–7:45, which overruns P-G3. Start at 6:50, or tick that item at 7:45 and tell P8.

**6.9 (7:00–7:20) Offline dry run.**
1. Turn Wi-Fi off and open `site/dist-single/index.html` from `file://`.
2. Walk the 60-second path below. Check that: L1–L5 run live in the browser, and L6–L8 show presets with banners; the badge is right; the scripted hints and the canned answers for the 3 demo questions appear; the Network panel shows no http(s) requests.
3. Then the **server-down variant**: Wi-Fi on, with `uvicorn` stopped or `VITE_API_BASE` pointing nowhere. The badge must go server, then preset, then in-browser one-mode.
4. Time both runs.
5. **The 60-second path**, which P8 formalizes:

| Time | Step |
|---|---|
| 0:00 | `#/learn` map |
| 0:05 | L4: predict C, ▶, the fringes appear |
| 0:20 | ask Schrö by voice, "why did the fringes fade?": `run_sim` chip and ✓, and the voice turns Photon loss on |
| 0:35 | L6 ▶ Run on Vultr: badge `server` or `preset`, the overshoot |
| 0:45 | L8: beat the square pulse, then claim the credential (explorer link) |
| 0:52 | Real Research: a provenance card, the Solana anchor, the community chart |
| 1:00 | end |

**6.10 (7:20–7:30) Freeze.** Tick P-G3 (§8), write `MERGE REQUESTED` with the final sha, and log `PRODUCT FROZEN at <sha> 7:30`. After that, no product code changes except fixes Harshit approves, and no new numbers.

## 7. Outputs
- **Branch:** `prod/p7-integrate` with the merged lanes and your wiring, and the copied presets and audio.
- **Deploy files:** `deploy/smoke.ps1`, `deploy/warm.sh`, and the `deploy/README.md` runbook.
- **Screenshots** in `docs/product/status/p7-shots/`.
- **Status file**, with these sections: the lanes table, merges, sent-backs and cuts; the deps applied (exact versions) and the routes; env values, with no secrets; the Harshit deploy block and deploy log; the local and public smoke tables; warm timings; the screenshot list; the Grok Bot prompt and issue checklist, with triage; the think-aloud table; the offline dry-run log, with timings; the P-G3 checklist; MERGE REQUESTED, PUSH REQUESTED, and open DECISION NEEDED items.
- **What you don't produce:** no physics outputs, records or numbers of your own. Latency figures are logged measurements, with command and output.

## 8. Acceptance gates
**P-G3** (PLAN §2): all must pass before DONE.
1. **Public URL:** all 8 levels play at the public URL, at desktop and 375 px, and the screenshots are saved.
2. **Offline:** L1–L5 work from `file://` with Wi-Fi off, and L6–L8 show presets with banners.
3. **Dry run:** it passes with the network off. The scripted hints and canned answers work, and the badge follows the correct order.
4. **Grok Bot:** its QA issues are triaged, and the issue checklist is in the status file.
5. **Think-aloud:** results recorded, with N stated (or timestamped "pending until 7:45").

**Plus:**
6. **Tests:** tests 1–3 are green; `& $env:DUQ_PY -m pytest server/tests -q` and `cd site; npm test` are green on the integration head; both builds pass test 5.
7. **Public smoke:** `smoke.ps1` against the public host passes every required check; feature SKIPs are explained. The warm 16×5 call takes < 15 s, and the repeat is cached.
8. **Sponsor features**, one visible each (PLAN never-cut): Gemini tutor (grounded answer), Vultr two-mode (or a preset with a badge), ElevenLabs voice (slider moved), Tiger (run in the chart), Solana (credential or anchor), Backboard (recap shown).
9. **Diff:** `git diff --name-only standard-track...HEAD` contains only merged lanes' allowlisted files plus §3 paths. No secrets are in git or `dist*`.
10. **Logged:** `MERGE REQUESTED` and the freeze. No push happened without Harshit's logged OK.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
git switch -c prod/p7-integrate standard-track; Copy-Item docs/plan/status/_TEMPLATE.md docs/product/status/p7-integrate.md
git diff --name-only standard-track...prod/<slug>                         # P1 allowlist
git show review/<slug>-r<N>:docs/plan/status/reviews/<slug>.md | Select-String "VERDICT|PASS|FAIL"
git merge --no-ff prod/<slug> -m "[p7-integrate] merge <slug>"; git diff --name-only --diff-filter=U
npm --prefix site install --save-exact blockly@<ver> @elevenlabs/client@<ver>
& $env:DUQ_PY -m pytest server/tests -q; cd site; npm test; cd ..
$env:VITE_API_BASE = "https://<ip-dashes>.sslip.io"; npm --prefix site run build; npm --prefix site run build:single
(Get-ChildItem site/dist-single).Name; (Get-Item site/dist-single/index.html).Length / 1MB
Select-String -Path site/dist/*,site/dist-single/* -Pattern "API_KEY|sk-[A-Za-z0-9]{16,}" -SimpleMatch:$false
& $env:DUQ_PY -m uvicorn server.app.main:app --port 8000          # local; then:
powershell -File deploy/smoke.ps1 -Base http://localhost:8000; powershell -File deploy/smoke.ps1 -Base https://<ip-dashes>.sslip.io
```
Harshit deploy block (bash on the VM, adapted to P0's `deploy/README.md`):
```bash
cd /opt/academy/repo && git fetch && git checkout <sha>      # first time: clone per HUMAN §2
# /opt/academy/.env (api: keys, ALLOWED_ORIGINS, API_HOST; NO SOLANA_SECRET_KEY_B58) and /opt/academy/chain.env (chain only) exist, Harshit-filled
cd deploy && docker compose --env-file /opt/academy/.env up -d --build && docker compose ps
curl -fsS https://<ip-dashes>.sslip.io/api/health
(crontab -l 2>/dev/null; echo '*/5 * * * * curl -fsS https://<ip-dashes>.sslip.io/api/health >/dev/null') | crontab -
bash deploy/warm.sh https://<ip-dashes>.sslip.io
```

## 10. Out of scope / do not
- **Don't fix lane code yourself.** Send it back. The only exceptions are your own wiring files and the generated copies.
- **Don't touch physics:** `src/`, `results/`, `figures/`, `site/src/data/live/**`, the Lab page logic, or l6's tests. Physics merges always take precedence.
- **Never handle Harshit's keys** or SSH credentials. Never commit `.env`, and never put a secret in a `VITE_*` variable.
- **Don't change the CONTRACT,** caps, timeouts or the live two-mode shape. Never raise a timeout to make a demo step pass; use the preset path.
- **Never push** or merge into `standard-track` without Harshit's logged OK. No mainnet, and no repo settings or visibility changes (that's Pranav).

## 11. If blocked (DECISION NEEDED + fallbacks + cut line)
> **Q:** CONTRACT/PLAN make the physics integrator the only writer of `standard-track`, but this lane is described as merging `prod/*` into it. **Options:** A) I integrate on `prod/p7-integrate` and the integrator merges that one branch. B) Harshit lets me merge into `standard-track` from the main checkout while the integrator is idle. **Recommendation:** A. **Blocking?** no: I'm integrating on my branch meanwhile.

> **Q:** The repo isn't public, so there is no GitHub Pages URL. **Options:** A) `npm run preview` on the demo laptop, plus the offline single-file build. B) Serve `site/dist` from Caddy on the VM (a P0 `Caddyfile` change). **Recommendation:** B if P0 agrees by 6:00, else A. **Blocking?** no.

**Other triggers:**
- The Worker isn't inlined in `dist-single` → send back to P1 (`?worker&inline`); meanwhile offline L1–L5 use presets; log it.
- A P2 badge hook is missing → send back to P2.
- A preset is missing for an L6 build or an L7 grid point → ask P0 to rerun `precompute.py` (never hand-make presets).
- A lane has no verdict by 5:15 → cut it per PLAN §3.
- Cold start > 60 s after a restart → run `warm.sh`, and never restart near the demo.

**Fallbacks:** VM down → demo on the single-file build with presets and scripted hints; voice fails → typed tutor questions; chain fails → "credential pending: retry" and show the existing anchor.

**Cut line:** PLAN §3 order (Pyodide → typed equation line → narrated mp3s → community chart → wallet connect → Grok Bot QA → server leaderboard recompute → Level 8), each logged as `CUT <item> at <time>`.
**Never cut:**
- L1–L5 offline;
- the tutor with sim tools and the guard (scripted fallback);
- the two-mode endpoint with preset fallback;
- one visible feature per core sponsor;
- any physics deliverable.

## 12. Hand-off (status contents + 3 questions Harshit should be able to answer — questions only)
**Status at DONE:**
- State and frozen sha.
- The lanes table (merged sha, CUT or sent back).
- Deps with exact versions, and routes.
- Local and public smoke tables, with warm and cached timings.
- The screenshot list.
- The Grok Bot checklist with triage.
- The think-aloud table (before/after, N).
- The offline dry-run log (timings, badge transitions).
- The P-G3 checklist.
- MERGE and PUSH requests with OK times.
- Open DECISION NEEDED items.

**Explain-back questions** (Harshit answers in `docs/defense.md`; do not write answers):
1. A judge turns the Wi-Fi off mid-demo on level 6. What exactly does the page show, where do those numbers come from, and how does the badge tell the judge it isn't a live simulation?
2. Why does the Academy keep one Vultr instance always on and warm, instead of starting a server per request or running two-mode in the browser? What would a cold start do to the demo?
3. How do you know a product merge didn't touch any physics file or weaken a physics result, and who is allowed to write `standard-track`?
