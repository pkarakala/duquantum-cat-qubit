"""Tutor memory client.

Live calls go through backboard-sdk:

    response = await client.send_message(text, memory="Auto", thread_id=...)

No API key keeps the labeled demo adapter. Tests inject a fake sdk and do not
open a socket. Memory is stored on the assistant, so each learner gets their own.
"""

from __future__ import annotations

import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://app.backboard.io/api"
RECAP_PROMPT = "In ≤ 2 sentences, recap this learner's misconceptions; then list ids"
SYSTEM_PROMPT = "Remember this learner's cat-qubit misconceptions. Do not invent physics numbers."


class UpstreamError(Exception):
    pass


def _model_kwargs() -> dict:
    """Optional BYOK model. Unset uses the SDK default, matching send_message(text, memory=...)."""
    provider = os.environ.get("BACKBOARD_LLM_PROVIDER", "").strip()
    if not provider or provider.lower() in ("off", "default"):
        return {}
    model = os.environ.get("BACKBOARD_MODEL", "").strip() or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    return {"llm_provider": provider, "model_name": model}


def _field(response, name: str) -> str:
    value = getattr(response, name, None)
    if value:
        return str(value)
    messages = getattr(response, "messages", None) or []
    for item in reversed(messages):
        raw = item.get(name) if isinstance(item, dict) else getattr(item, name, None)
        if raw:
            return str(raw)
    return ""


class BackboardClient:
    """Sync facade over ``backboard.BackboardClient.send_message``.

    FastAPI runs these handlers off the event loop, so each call uses ``asyncio.run``.
    Pass ``sdk`` in tests. A real client is built only when ``sdk`` is omitted, and it
    is closed before the call returns so it is not reused on another loop.
    """

    def __init__(self, api_key: str, base: str = BASE_URL, store=None, sdk=None):
        self.api_key = api_key
        self.base = base.rstrip("/")
        self.store = store
        self._sdk = sdk
        self._learner_id: str | None = None

    def ensure_thread(self, learner_id: str) -> str:
        self._learner_id = learner_id
        if self.store is None:
            return ""
        return self.store.get_thread(learner_id) or ""

    def add_message(self, thread_id: str, content: str, memory: str = "Auto") -> dict:
        created = not thread_id
        try:
            response = self._run(self._send(content, memory, thread_id or ""))
        except UpstreamError:
            raise
        except Exception as exc:
            raise UpstreamError(str(exc)) from exc
        new_thread = _field(response, "thread_id")
        if not new_thread:
            raise UpstreamError("backboard returned no thread_id")
        if created and self.store is not None and self._learner_id:
            self.store.set_thread(self._learner_id, new_thread)
            assistant_id = _field(response, "assistant_id")
            if assistant_id:
                self.store.set_meta(f"backboard_assistant:{self._learner_id}", assistant_id)
        return {"content": _field(response, "content"), "thread_id": new_thread, "memory": memory}

    def ask(self, thread_id: str, prompt: str | None = None, memory: str = "Readonly") -> str:
        data = self.add_message(thread_id, prompt or RECAP_PROMPT, memory=memory)
        return data.get("content") or ""

    async def _send(self, text: str, memory: str, thread_id: str):
        sdk = self._sdk
        close = None
        if sdk is None:
            try:
                from backboard import BackboardClient as SdkClient
            except ImportError as exc:
                raise UpstreamError("backboard-sdk is not installed") from exc
            sdk = SdkClient(api_key=self.api_key, base_url=self.base, timeout=30)
            close = sdk.aclose
        try:
            kwargs = {"memory": memory, "stream": False, "system_prompt": SYSTEM_PROMPT}
            if thread_id:
                kwargs["thread_id"] = thread_id
            elif self.store is not None and self._learner_id:
                assistant_id = self.store.get_meta(f"backboard_assistant:{self._learner_id}")
                if assistant_id:
                    kwargs["assistant_id"] = assistant_id
            model = _model_kwargs()
            kwargs.update(model)
            try:
                return await sdk.send_message(text, **kwargs)
            except Exception as exc:
                status = getattr(exc, "status_code", None)
                # A rejected BYOK model falls back to Backboard's default. Timeouts do not retry.
                if model and isinstance(status, int) and 400 <= status < 500:
                    kwargs.pop("llm_provider", None)
                    kwargs.pop("model_name", None)
                    return await sdk.send_message(text, **kwargs)
                raise
        finally:
            if close is not None:
                await close()

    def _run(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()


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
            return "Demo memory: Demo mode: no misconceptions stored yet."
        listed = ", ".join(ids)
        return f"Demo memory: Demo mode: this learner is still carrying {listed}. Those ideas are still open."
