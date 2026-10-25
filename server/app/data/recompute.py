"""Re-score unverified leaderboard rows once src.linresp can be imported.

A match stores the server score with verified true. A mismatch sets
payload.rejected and drops out of the public leaderboard. Rows are not deleted.
"""

from __future__ import annotations

import argparse
import os

from server.app.data.challenge import CHALLENGE, T_US, scores_match, server_score
from server.app.data.migrate import load_env_file, redact


def run(store, challenge: str = CHALLENGE) -> dict:
    """Flip matching unverified rows to verified and reject tampered ones."""
    verified = rejected = skipped = 0
    rows = list(store.unverified_rows(challenge))
    for row in rows:
        payload = row.get("payload") or {}
        eps = payload.get("eps_over_g2")
        if not isinstance(eps, list) or not eps:
            skipped += 1
            continue
        try:
            computed = server_score(eps)
        except ImportError:
            return {
                "verified": verified,
                "rejected": rejected,
                "skipped": skipped,
                "linresp": False,
            }
        client = float(row["score"])
        stored = {
            "T_us": float(payload.get("T_us", T_US)),
            "eps_over_g2": [float(x) for x in eps],
            "client_score": float(payload.get("client_score", client)),
            "source": "linresp",
        }
        if scores_match(client, computed):
            stored["verified"] = True
            stored["rejected"] = False
            store.update_leaderboard(row, score=float(computed), verified=True, payload=stored)
            verified += 1
        else:
            stored["verified"] = False
            stored["rejected"] = True
            stored["source"] = "client"
            store.update_leaderboard(row, score=client, verified=False, payload=stored)
            rejected += 1
    return {"verified": verified, "rejected": rejected, "skipped": skipped, "linresp": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-score unverified readout-pulse rows")
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--challenge", default=CHALLENGE)
    args = parser.parse_args(argv)
    if args.env_file:
        load_env_file(args.env_file)
    from server.app.data.db import get_store

    store = get_store()
    if store is None:
        print("TIGER_DATABASE_URL is unset; recompute skipped")
        return 2
    try:
        result = run(store, args.challenge)
    except Exception as exc:
        print("recompute failed:", redact(exc))
        return 1
    print(
        f"recompute verified={result['verified']} rejected={result['rejected']} "
        f"skipped={result['skipped']} linresp={result['linresp']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
