"""Backboard client, plus a labeled demo adapter.

Verified endpoints (docs.backboard.io, Oct 2026):
- POST {base}/assistants
- POST {base}/assistants/{assistant_id}/threads
- POST {base}/threads/{thread_id}/messages   body.memory = "Auto" | "Readonly"
Header: X-API-Key. Base default https://app.backboard.io/api.
"""

from __future__ import annotations

import os
import re

BASE_URL = "https://app.backboard.io/api"
RECAP_PROMPT = "In ≤ 2 sentences, recap this learner's misconceptions; then list ids"


class UpstreamError(Exception):
    pass


class BackboardClient:
    def __init__(self, api_key: str, base: str = BASE_URL, transport=None, store=None):
        self.api_key = api_key
        self.base = base.rstrip("/")
        self._transport = transport
        self.store = store

    def _http(self):
        import httpx

        return httpx.Client(
            base_url=self.base,
            timeout=3.0,
            transport=self._transport,
            headers={"X-API-Key": self.api_key},
        )

    def _post(self, path: str, payload: dict) -> dict:
        try:
            with self._http() as client:
                response = client.post(path, json=payload)
        except Exception as exc:
            raise UpstreamError(str(exc)) from exc
        if response.status_code >= 400:
            raise UpstreamError(f"backboard {response.status_code}")
        return response.json()

    def ensure_assistant(self) -> str:
        if self.store is not None:
            cached = self.store.get_meta("backboard_assistant_id")
            if cached:
                return cached
        created = self._post(
            "/assistants",
            {
                "name": "Schro",
                "system_prompt": "Remember this learner's cat-qubit misconceptions. Do not invent physics numbers.",
            },
        )
        assistant_id = created["assistant_id"]
        if self.store is not None:
            self.store.set_meta("backboard_assistant_id", assistant_id)
        return assistant_id

    def ensure_thread(self, learner_id: str) -> str:
        if self.store is not None:
            existing = self.store.get_thread(learner_id)
            if existing:
                return existing
        assistant_id = self.ensure_assistant()
        created = self._post(f"/assistants/{assistant_id}/threads", {})
        thread_id = created["thread_id"]
        if self.store is not None:
            self.store.set_thread(learner_id, thread_id)
        return thread_id

    def add_message(self, thread_id: str, content: str, memory: str = "Auto") -> dict:
        payload = {"content": content, "memory": memory, "stream": False}
        model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        # BYOK Gemini when Backboard accepts it. A 4xx retries on Backboard's default model.
        payload["llm_provider"] = os.environ.get("BACKBOARD_LLM_PROVIDER", "google")
        payload["model_name"] = model
        try:
            return self._post(f"/threads/{thread_id}/messages", payload)
        except UpstreamError as exc:
            # A rejected BYOK model falls back to Backboard's default. Timeouts do not retry.
            if "backboard 4" not in str(exc):
                raise
            payload.pop("llm_provider", None)
            payload.pop("model_name", None)
            return self._post(f"/threads/{thread_id}/messages", payload)

    def ask(self, thread_id: str, prompt: str | None = None, memory: str = "Readonly") -> str:
        data = self.add_message(thread_id, prompt or RECAP_PROMPT, memory=memory)
        return data.get("content") or ""


class DemoBackboardClient:
    """In-process stand-in. Every payload is tagged demo-adapter so it cannot be mistaken for Backboard."""

    label = "demo-adapter"

    def __init__(self, store):
        self.store = store

    def ensure_thread(self, learner_id: str) -> str:
        existing = self.store.get_thread(learner_id)
        if existing:
            return existing
        thread_id = f"demo-{learner_id}"
        self.store.set_thread(learner_id, thread_id)
        return thread_id

    def add_message(self, thread_id: str, content: str, memory: str = "Auto") -> dict:
        self.store.add_demo_message(thread_id, content, memory)
        return {"content": content, "memory": memory, "source": self.label}

    def ask(self, thread_id: str, prompt: str | None = None, memory: str = "Readonly") -> str:
        notes = self.store.demo_messages(thread_id)
        ids: list[str] = []
        for note in notes:
            for mid in re.findall(r"M[1-7]", note):
                if mid not in ids:
                    ids.append(mid)
        if not ids:
            return "Demo memory: no misconceptions stored yet."
        listed = ", ".join(ids)
        return f"Demo memory: this learner is still carrying {listed}. Those ideas are still open."
