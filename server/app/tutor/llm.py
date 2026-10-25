"""Gemini, with automatic function calling off. Tests use FakeLLM and never touch the network."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    function_calls: list = field(default_factory=list)
    text: str = ""
    data: dict | None = None


FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "hint_level": {"type": "integer"},
        "numbers_cited": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reply", "hint_level"],
}


class FakeLLM:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def complete(self, messages, *, tools=None, schema=None, images=None):
        self.calls.append({"messages": messages, "tools": tools, "schema": schema, "images": images})
        if not self.script:
            raise RuntimeError("FakeLLM script exhausted")
        step = self.script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return LLMResponse(
            function_calls=list(step.get("function_calls") or []),
            text=step.get("text") or "",
            data=step.get("json"),
        )


class GeminiLLM:
    """One generate_content call tries tools and schema together. A rejection switches to two phases."""

    phase = "one-phase"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

    def complete(self, messages, *, tools=None, schema=None, images=None):
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self.api_key,
            # Milliseconds. Two attempts ride out transient 503s; the 25 s turn deadline still caps it.
            # The API rejects a server deadline under 10s.
            http_options=types.HttpOptions(timeout=12000, retry_options=types.HttpRetryOptions(attempts=2)),
        )
        contents = _contents(messages, images, types)
        config = _config(types, tools, schema, together=GeminiLLM.phase == "one-phase")
        try:
            response = client.models.generate_content(model=self.model, contents=contents, config=config)
        except Exception as exc:
            # Only a rejected combination of tools and schema is retried. A quota error must not be sent twice.
            status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
            # A missing thought_signature is fixed by echoing the part, not by dropping the schema.
            if "thought_signature" in str(exc):
                raise
            if tools and schema and GeminiLLM.phase == "one-phase" and status in {400, 404}:
                GeminiLLM.phase = "two-phase"
                config = _config(types, tools, schema, together=False)
                response = client.models.generate_content(model=self.model, contents=contents, config=config)
            else:
                raise
        return _parse(response)


def _config(types, tools, schema, *, together: bool):
    kwargs = {
        "temperature": 0.4,
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        "thinking_config": types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
    }
    if tools:
        kwargs["tools"] = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters_json_schema=tool["parameters"],
                    )
                    for tool in tools
                ]
            )
        ]
    # Two-phase: schema only on the call that has no tools. One-phase: both at once.
    if schema and (together or not tools):
        kwargs["response_mime_type"] = "application/json"
        kwargs["response_schema"] = schema
    return types.GenerateContentConfig(**kwargs)


def _contents(messages, images, types):
    contents = []
    for index, message in enumerate(messages):
        parts = []
        if message.get("text"):
            parts.append(types.Part(text=message["text"]))
        if index == 0 and images:
            for image in images:
                parts.append(types.Part.from_bytes(data=image["data"], mime_type=image.get("mime", "image/png")))
        for call in message.get("function_calls") or []:
            # Gemini 3 requires the original thought_signature when the call is sent back.
            part_kwargs = {}
            if call.get("thought_signature") is not None:
                part_kwargs["thought_signature"] = call["thought_signature"]
            parts.append(
                types.Part(
                    function_call=types.FunctionCall(name=call["name"], args=call.get("args") or {}),
                    **part_kwargs,
                )
            )
        for item in message.get("function_responses") or []:
            parts.append(types.Part.from_function_response(name=item["name"], response=item["response"]))
        role = "model" if message.get("role") == "model" else "user"
        contents.append(types.Content(role=role, parts=parts or [types.Part(text="")]))
    return contents


def _parse(response) -> LLMResponse:
    calls = []
    texts = []
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return LLMResponse(text=getattr(response, "text", "") or "")
    parts = getattr(candidates[0].content, "parts", None) or []
    for part in parts:
        function_call = getattr(part, "function_call", None)
        if function_call is not None and getattr(function_call, "name", None):
            args = function_call.args or {}
            calls.append(
                {
                    "name": function_call.name,
                    "args": dict(args),
                    "thought_signature": getattr(part, "thought_signature", None),
                }
            )
        elif getattr(part, "text", None):
            texts.append(part.text)
    text = "\n".join(texts).strip()
    data = None
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            data = parsed
    return LLMResponse(function_calls=calls, text=text, data=data)
