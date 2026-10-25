# Academy deploy

Vultr is **demo mode** in this checkout: there is no Vultr API key and no instance. This compose file is the production interface. Solana (the `chain` service) and Backboard are also demo until their secrets exist. Gemini, ElevenLabs, and Tiger Data are read from `/opt/academy/.env` and are live when those keys are set.

The api container must not receive `SOLANA_SECRET_KEY_B58`. That key belongs in `/opt/academy/chain.env` only.

## Bring up

From `deploy/` on the VM:

```bash
apt update && apt install -y docker.io docker-compose-v2 git
# clone the repo, then:
cd deploy
docker compose --env-file /opt/academy/.env up -d --build
```

`API_HOST` is the dashed IPv4 plus `.sslip.io`, for example `45-76-1-2.sslip.io`. Caddy obtains TLS for that name. Put the same origin in `ALLOWED_ORIGINS` and in the site's `VITE_API_BASE`.

## Smoke

```bash
curl -s https://$API_HOST/api/health
docker compose logs -f api
```

`features.gemini`, `features.elevenlabs`, and `features.tiger` are true when those keys are in the api env. `features.chain` is true only after the chain service answers `GET /api/chain/health`. `integrations.vultr`, `integrations.solana`, and `integrations.backboard` stay `demo` until those credentials exist. Demo Solana responses keep `tx_sig: null` and `demo_mode: true`. They are not fake transactions.

## After a restart

The api process warms the live shapes on startup (one-mode N=30, two-mode 16×5 with 201 samples) and writes the JAX cache to the `jax-cache` volume. The healthcheck allows 180s for that. To warm again:

```bash
docker compose restart api
docker compose logs -f api
```

Watch for the `startup warmup` line before pointing a demo at a two-mode level.
