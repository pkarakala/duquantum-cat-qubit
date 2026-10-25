# Handover: future work and sponsor research (Oct 25 2026, 16:50 UTC)

Thread: "Research future work and sponsor ideas". Status: STOPPED at Pranav's request. No repo changes were made by this thread.
The deep-research agents all failed (session usage limit, resets 17:20 UTC), so there is no full report and no HTML artifact yet.
Everything below was checked by me with web search unless marked "unverified".

## Ranked future-work lines (say aloud; 5-8 are next steps, not live)
1. Scale to a logical qubit: feed our Γ_X, Γ_Z and 0.65% readout error into a repetition-code error budget (A&B's line of cats with a phase-flip code) and work out how many cats reach a target logical error.
2. Self-calibrating readout: make the −23 MHz Stark retune a fitted parameter, then tune pump detuning and pulse shape together with jax.grad under bandwidth limits.
3. Find where Γ_X saturates: add thermal photons, Kerr, non-RWA terms (real devices stop improving exponentially).
4. Squeezed "moon" cats: A&B measured bit-flip time 138 ms → 22 s at the same 1.3 µs phase-flip time (n̄ 4.9 vs 4.1, λ=1.04), arXiv:2502.07892. We already tried moon cats for inflation only (no gain); readout/Γ_X with squeezing is new.
5. ElevenLabs Talk: voice agent whose client tools move the α² slider and rerun the sim (agent created and wired on integrated 5752a27; not yet on the live Vultr site; Gemini as its LLM is unverified).
6. Tiger Data: hypertable of every learner and research run; continuous aggregate → live class dashboard + public provenance of every run.
7. Backboard: per-learner misconception memory → adaptive next level and hint level.
8. Solana: move offline demo → devnet soulbound certificate + results-hash Memo anchor ("verifiable science").
Honesty: Talk is now wired to an ElevenLabs agent on branch integrated (5752a27, agent_0201m5syr24geva8w2vnjhg36k89, public, dynamic vars, 5 client tools) but the live Vultr site is still on 8da0773 until Pranav redeploys, see handover/product-layer.md; Solana is offline demo (not broadcast); Backboard is demo without a key; no Tiger chart in the UI.

## Talk (ElevenLabs agent) setup checklist
UPDATE 16:52 UTC: another thread already created the agent and wired it (integrated 5752a27). Use this list to check that work, mainly steps 3-6.
Code: origin/integrated site/src/tutor/voice-sdk.ts (Conversation.startSession with clientTools set_param, run_sim, show_hint, next_level); env VITE_ELEVENLABS_AGENT_ID; server .env has ELEVENLABS_API_KEY / VOICE_ID / AGENT_ID.
1. Create an agent in the ElevenLabs Agents dashboard: system prompt (Socratic tutor, never gives the answer first, cites sim numbers), first message, voice.
2. LLM: pick a Google/Gemini model in the agent's LLM settings (docs say Google models are offered; exact Gemini model name unverified).
3. Add four CLIENT tools with names and parameter schemas that exactly match the code (set_param, run_sim, show_hint, next_level). Mark run_sim as blocking / "wait for response" so the agent waits for the sim result; the returned string goes back to the agent.
4. Check SDK: one doc mirror registers clientTools on the conversation hook/object rather than as a startSession option. Test that our startSession({agentId, clientTools}) call actually registers them (possible bug).
5. Auth: public agent + domain allowlist (66-42-119-3.sslip.io), or better a signed URL minted by our FastAPI server with the API key (URL expires after 15 min; never ship the key to the browser).
6. Personalize: put {{learner_recap}}, {{level_id}}, {{mastery}} dynamic variables in the system prompt and pass them at session start (dynamic variables are the recommended approach; overrides are legacy and must be enabled in security settings).
7. Optional: knowledge base/RAG with docs/task_1.md and docs/task_2.md (RAG needs docs over 500 bytes; 20 MB cap on non-enterprise).
8. Set VITE_ELEVENLABS_AGENT_ID, rebuild site, redeploy Vultr (deploy script on Pranav's Mac).

## Learner adaptation, minimum version (~4-8 h)
- Log each prediction with misconception_id (tutor_events table already exists in server/app/data/db.py).
- Per-concept mastery with Bayesian Knowledge Tracing (4 params: P(L0), P(T), guess, slip; keep guess < 0.3, slip < 0.1 per Corbett & Anderson). Mastery picks hint level and whether to unlock the next level.
- Backboard: memory "Auto" when writing outcomes, "Readonly" when reading the recap; memories are scoped per assistant (so use one assistant per learner, or tag memories by learner).
- Feed the recap to the Gemini tutor and into the Talk agent's dynamic variables.
- Evidence to cite: Kestin et al., Scientific Reports 15, 17458 (2025): Harvard physics RCT, 194 students, AI tutor built on research-based scaffolding beat in-class active learning, learned more in less time (two-week study; scaffolding is the active ingredient).

## Sources found
- A&B roadmap (Dec 2024 white paper; Boson → Helium → Lithium → … → Graphene, 100 logical qubits by 2030): https://thequantuminsider.com/2024/12/04/from-cat-qubits-to-universal-quantum-computing-alice-bobs-2030-roadmap-delivers-high-fidelity-solutions/
- Helium Quantum System (June 11 2026): first logical qubit with as few as 18 cat qubits; next chip 48 cat qubits: https://thequantuminsider.com/2026/06/11/alice-bob-unveils-first-quantum-system-available-for-research-partners/
- Réglade et al., Nature 629, 778 (2024): bit-flip > 10 s, phase-flip > 490 ns.
- Le Régent et al., Quantum 7, 1198 (2023), repetition cat code with fast noisy CNOTs: https://quantum-journal.org/papers/q-2023-12-06-1198/
- Ruiz et al., LDPC-cat codes, Nat. Commun. 16, 1040 (2025): 100 logical qubits on 758 cats at ~0.1% phase-flip, ε_L ≤ 1e-8: https://pmc.ncbi.nlm.nih.gov/articles/PMC11762751/
- Rousseau et al., squeezing, arXiv:2502.07892.
- ElevenLabs: personalization/dynamic variables https://elevenlabs.io/docs/eleven-agents/customization/personalization ; authentication https://elevenlabs.io/docs/eleven-agents/customization/authentication ; RAG https://elevenlabs.io/docs/conversational-ai/customization/knowledge-base/rag
- Gemini Live API get-started (function calling in live sessions): https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk
- Backboard memory: https://docs.backboard.io/concepts/memory
- Tiger continuous aggregates: https://www.tigerdata.com/docs/use-timescale/latest/continuous-aggregates/create-a-continuous-aggregate
- Kestin et al. 2025: https://pmc.ncbi.nlm.nih.gov/articles/PMC12179260/

## Left to do (next Claude)
- Not yet researched: Vultr GPU fp64 options, Solana devnet Memo/Metaplex Core current docs, Cursor/Grok Bot, DEV rules, past MLH winners.
- Optional: rerun the deep-research workflow after 17:20 UTC (script: /root/.claude/projects/-home-user-duquantum-cat-qubit/28bfa950-9e38-5c49-bf0f-9e559da37efa/workflows/scripts/future-work-sponsor-research-wf_7ed97193-271.js, container-local, may be gone), then publish an HTML report.
- Optional: add a short docs/future_work.md to the repo via PR (Pranav merges).
