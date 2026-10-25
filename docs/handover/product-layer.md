# Product layer handover (Oct 25 2026, 16:48 UTC)

1. Demo branch is `integrated` (commit straight to it, no PRs, per Pranav). PR #15 (main) is a stale draft.
2. Live site: https://66-42-119-3.sslip.io (Vultr 66.42.119.3). It last deployed 8da0773 and ALL PASSED. Newer commits (Sandbox, Talk, lab pages, README, Vultr-live flag) need a redeploy.
3. Redeploy (Pranav runs it on his Mac): /private/tmp/claude-501/-Users-pkarakala-projects-duquantum-cat-qubit--claude-worktrees-great-solomon-5339e3/c1817dde-7741-4258-9e56-ebf4515c696f/scratchpad/redeploy_vultr.sh (it fetches origin/integrated and symlinks demo-integrated/site/node_modules).
4. Local demo on the Mac: ~/projects/duquantum-cat-qubit/demo-integrated, site on :5180, API on :8001 (:8000 is qubit-lab, don't touch).
5. Talk is the ElevenLabs agent agent_0201m5syr24geva8w2vnjhg36k89 (public; default in site/src/tutor/voice-sdk.ts). Dynamic vars: level, failed checks, Backboard recap. Needs mic Allow.
6. Keys live only in .env on the Mac and the VM (/opt/academy/.env). Never commit them. Rotate all keys after judging (they were pasted in chat).
7. Open: L5 and L7 presets are hand-made mocks (L5 Γ_X is 295× off main; the L7 cost card is now labelled illustrative). Fix: load from results/ via site/scripts/export_results.py, or keep them out of the demo.
8. Avoid in the demo: L5/L7 numbers. Solana is demo-only (signed locally, not broadcast).
9. 4 site tests fail on integrated before these changes (sim physics/linresp parity); not caused by this work.
10. Docs: README.md on integrated is the Academy README; docs/product/status/DEMO_CHECKLIST.md is older than this note, so this note wins.
