# Handover: Academy home page + research pages (branch `integrated`, last push 8cb04ae)
1. Home `#/` = the talk, in walkthrough-script order: `site/src/academy/home.ts` (`SLIDES`, `SPONSORS`), figures `site/public/talk/` (from the submitted deck PDF). ←/→ steps sections.
2. Research `#/research` (`research.ts`) + lab pages `#/inflate #/errors #/readout #/verify` (`labPages.ts`): main's real figures/numbers only.
3. Static research files `site/public/research/` built by `python site/scripts/build_research.py <main checkout>` (needs markdown, nbconvert). Last built from main @ f454560.
4. Leaderboard `#/challenge` (`showChallenge` in routes.ts): live API rows, else 3 rows labelled as samples.
5. Nav in `site/index.html`. Docs: README "Pages" table + `docs/product/SITE_PAGES.md`.
6. Rule (Pranav): commit site work straight to `integrated`, no PRs, no force-push, no Claude co-author lines; author "Pranav Reddy <preddy@ucsb.edu>".
7. Build: `cd site && npm ci && npm run build` passes (npm ci needed for new @elevenlabs/client). Academy vitest 37/37; 4 src/sim tests fail on integrated itself (pre-existing).
8. Open: Vultr redeploy of integrated (product-layer thread owns it); results pages #/bitflips etc. exist only on PR #15.
9. Open: rerun build_research.py if main's docs/notebooks change again.
10. Solana is demo only: never claim otherwise.
