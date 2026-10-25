# Sponsor blurbs

One blurb per MLH category, in submission order. Each describes the app on `prod/p7-integrate` at the integration commit, not the plan. Harshit submits. This lane does not.

## Gemini

Schrö answers through `POST /api/tutor` only after a simulator tool has run. The tools are `run_sim`, `get_level_state`, `get_record`, `lookup_grid`, and `check`, and the number guard removes a quantity that a tool, a record, the learner state, or a level constant does not already back. A learner sees the cited source instead of a number the model invented. Gemini is live when its key is set.

## ElevenLabs

Spoken audio uses `POST /api/voice/tts`. The page also exposes the client tools `set_param`, `run_sim`, `show_hint`, `next_level`, and `ask_tutor`, and `ask_tutor` returns only the guarded tutor reply so a learner hears the same check. No agent id was set on this branch, so no ElevenAgents session was opened. Concept-card audio files are not in the tree, and the card falls back to text.

## Vultr

`POST /api/sim/one_mode`, `POST /api/sim/two_mode`, and `POST /api/sim/expr` run dynamiqs in the API process, which is how a learner reaches a two-mode model the browser cannot host. Health labels Vultr demo, and no Vultr host was deployed. A successful API response is badged Live · Vultr dynamiqs, which names the intended host rather than a machine in this run. Common builds stay precomputed, and the source badge stays visible.

## Tiger Data

Finished runs go to `POST /api/runs`, and the room chart is `GET /api/community/alpha` on the `alpha_choices_5m` continuous aggregate of the `sim_runs` hypertable. `GET /api/leaderboard` and `GET /api/progress` are the other learner views, and rows do not store a name or an email. Timescale is live when the database URL is set. With no URL, a run can still reach the in-process sink, and that sink is not a hosted chart.

## Solana

`POST /api/chain/credential` builds a soulbound credential request, and `POST /api/chain/anchor` is the Memo path for a hash of the results index. On this branch the credential answer is demo mode with no transaction signature, and nothing was broadcast. Solana is devnet only, with no real funds, so a learner is not asked to pay. The claim slot shows that demo state instead of an explorer link.

## Backboard

`POST /api/memory/event` and `GET /api/memory/recap` are the memory routes. With no Backboard key they answer from the labeled demo adapter, so a learner sees a recap that is not a stored Backboard thread. Gemini calls for the tutor stay direct. Misconception memory is the feature, and it is not live here.

## SpaceXSI

The Academy was built with Cursor agent lanes, using the briefs in `docs/product/briefs/` and `docs/plan/briefs/`. Grok Bot was the planned QA walk of the levels, and that walk was not run on this branch. Harshit should tick the raffle opt-in when submitting this category. That process is what a later team can learn from, and this lane does not submit it.

## DEV

The writing-challenge draft sits beside this file, so another builder can learn why the tutor has to run the simulation before it answers. Note: publish after the event, by Oct 31 11:59 PM ET (within the month), and include the tag `#mlhacks`. Harshit publishes it, and this lane does not.
