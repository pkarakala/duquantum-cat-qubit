# Harshit-only tasks for the Academy phase

Agents can't create accounts or handle your keys. These steps are yours. Keep keys out of chat and out of git: put them only in `server/.env` locally, and in the VM's `.env`.

## 1. Accounts and keys (about 45 min, start now)
| # | Do | Result → where it goes |
|---|---|---|
| 1 | **Gemini:** go to aistudio.google.com, then "Get API key". The free tier is fine. | `GEMINI_API_KEY` |
| 2 | **Vultr:** register at **discover.vultr.com/mlh** (school as Company, "Student" as Job Title). Wait for the promo email, then Billing → Gift Code for $100. Deploy a **CPU-Optimized** Ubuntu 24.04 instance with 4 vCPU and 8 GB, add your SSH key, and note the IPv4. | VM IP; `ssh root@<ip>` works |
| 3 | **ElevenLabs:** sign up, apply the promo (Creator month) if the email arrived, create an API key, pick a voice, and create an **ElevenAgent**: public, auth off, LLM = Gemini 3.8 Flash. Lane P4 adds the client tools. | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_AGENT_ID` |
| 4 | **Tiger Data:** sign up for Tiger Cloud ($1,000 / 30 days, no card), create a service, and copy the connection string. | `TIGER_DATABASE_URL` |
| 5 | **Backboard:** sign up at app.backboard.io/hackathon/signup with code **DUQUANTUM**, then create an API key. | `BACKBOARD_API_KEY` |
| 6 | **Solana devnet:** install Phantom (or `solana-keygen new`), switch to **devnet**, and airdrop at faucet.solana.com. Create a separate server keypair for minting: devnet only, never real funds. | `SOLANA_SECRET_KEY_B58` (server only) |
| 7 | **Cursor Pro + Grok Bot:** redeem the MLH promo (email or MLH coach) and enable Grok Bot. | Needed for the SpaceXSI raffle |
| 8 | `ADMIN_TOKEN`: any long random string, used for the anchor endpoint. | `.env` |

Then copy `server/.env.example` to `server/.env`, fill it in, and paste the same file on the VM at `/opt/academy/.env`.

## 2. Vultr deploy (lane P7 does the work; you approve and run any command that needs your SSH)
- `ssh root@<ip>`, then:
  - `apt update && apt install -y docker.io docker-compose-v2 git`
  - `git clone` the repo (it's private until Pranav makes it public, so use a deploy key or a token you create yourself)
  - `cd deploy && docker compose --env-file /opt/academy/.env up -d --build`
  - The api container reads `/opt/academy/.env`, which has no Solana key. The chain container reads `/opt/academy/chain.env` (CONTRACT §2).
- Caddy serves `https://<ip-with-dashes>.sslip.io`. Put that URL in the site's `VITE_API_BASE` and in `ALLOWED_ORIGINS`.
- Smoke test: `curl https://<host>/api/health`.

## 3. Think-aloud tests (7:00 to 7:45 AM; 10 min each with 2–3 non-physics hackers)
1. "Please think out loud." Let them play L2 to L4 without help.
2. Note each prediction (right or wrong, and the misconception ID). Note where they got stuck, and quote what they said.
3. After L4, re-ask the L3 and L4 prediction questions. Record before and after accuracy (N is small; say so).
4. Put the results table in `docs/product/status/p7-integrate.md`. This is the "learning and growth" evidence.

## 4. Submissions (by 10:45 AM; see `SPONSORS.md` checklist)
- **Devpost:** add the Academy URL and the "Built with" list.
- **MLH challenges:** submit once per category (Gemini, ElevenLabs, Vultr, Tiger Data, Solana, Backboard, SpaceXSI with the raffle opt-in, DEV later). Use the P8 write-ups.
- **Video:** add the Academy segment (60-second demo; `docs/product/demo_script.md`).

## 5. Sleep
You now carry both phases, so protect a block of about **2:30 to 6:00 AM**. Before you sleep:
- The physics queue is running.
- Product wave 2 is launched.
- Nothing is waiting on you in any `DECISION NEEDED`.
