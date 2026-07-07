"""Thin OpenAI wrapper supporting chat + tool-calling, with an offline mock.

If `openai` is installed AND OPENAI_API_KEY is set, real calls are made and the
real `usage` token counts are returned. Otherwise a deterministic mock kicks in
so the whole experiment still runs (and produces sensible, reproducible numbers)
with zero network and zero spend. The mock is clearly flagged via `.live`.
"""
from __future__ import annotations
import os
import json
import hashlib
import re
from dataclasses import dataclass, field

from .token_utils import count_tokens

try:
    from openai import OpenAI  # type: ignore
    _HAS_OPENAI = True
except Exception:  # pragma: no cover
    OpenAI = None
    _HAS_OPENAI = False


@dataclass
class LLMResponse:
    text: str
    tool_calls: list = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    live: bool = False


# --- deterministic mock helpers -------------------------------------------
_FILLERS = [
    r"\bthank you so much\b", r"\bthanks a lot\b", r"\bso much\b",
    r"\bvery much\b", r"\ba lot\b",
    r"\bcan you please\b", r"\bcould you please\b", r"\bplease\b",
    r"\bcan you\b", r"\bcould you\b", r"\bwould you\b",
    r"\bwould you be able to\b", r"\bi want you to\b",
    r"\bi would like you to\b", r"\bi'd like you to\b",
    r"\bi would really like you to\b", r"\bfor me\b",
    r"\bkindly\b", r"\bif you don't mind\b", r"\bi was wondering if\b",
    r"\bi'd like\b", r"\bthank you\b", r"\bthanks\b", r"\bif possible\b",
    r"\bjust\b", r"\bin order to\b", r"\bbe sure to\b",
    r"\bmake sure to\b", r"\bmake sure that you\b", r"\bplease make sure\b",
    r"\bvery best\b", r"\bat all times\b", r"\bas possible\b",
]


def _cleanup(s: str) -> str:
    s = re.sub(r"\s+([?.!,;:])", r"\1", s)        # attach punctuation
    s = re.sub(r"[,;:]+([?.!])", r"\1", s)         # comma before ? . ! -> drop comma
    s = re.sub(r"([?.!])[?.!]+", r"\1", s)         # collapse repeated end-punct
    s = re.sub(r"\s+", " ", s).strip(" ,;:")
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    return s


_LIGHT_FILLERS = [
    r"\bthank you so much\b", r"\bthanks a lot\b", r"\bso much\b",
    r"\bcan you please\b", r"\bcould you please\b", r"\bplease\b",
    r"\bkindly\b", r"\bthank you\b", r"\bthanks\b", r"\bfor me\b",
]


def _light_compress(text: str) -> str:
    """Conservative rule-based strip: only obvious politeness markers."""
    out = text
    for pat in _LIGHT_FILLERS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return _cleanup(out) or text


def _mock_compress(text: str, aggressive: bool = False) -> str:
    out = text
    for pat in _FILLERS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    out = _cleanup(out)
    if aggressive:
        # Drop articles and collapse remaining filler.
        out = re.sub(r"\b(a|an|the)\b", "", out, flags=re.IGNORECASE)
        out = _cleanup(out)
    return out or text


def _seed(text: str) -> float:
    h = hashlib.sha256(text.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


class LLMClient:
    def __init__(self, model: str | None = None):
        self.model = model
        self.live = _HAS_OPENAI and bool(os.environ.get("OPENAI_API_KEY"))
        self._client = OpenAI() if self.live else None

    # -- plain chat ---------------------------------------------------------
    def chat(self, messages: list[dict], model: str | None = None,
             temperature: float = 0.2) -> LLMResponse:
        model = model or self.model
        if self.live:
            r = self._client.chat.completions.create(
                model=model, messages=messages, temperature=temperature,
            )
            return LLMResponse(
                text=r.choices[0].message.content or "",
                input_tokens=r.usage.prompt_tokens,
                output_tokens=r.usage.completion_tokens,
                live=True,
            )
        # ---- mock ----
        user = next((m["content"] for m in reversed(messages)
                     if m["role"] == "user"), "")
        sys = next((m["content"] for m in messages if m["role"] == "system"), "")
        if "rewrite" in sys.lower() or "compress" in sys.lower():
            # A real LLM rewrite is typically more thorough than a regex strip,
            # so the mock applies the aggressive compressor here.
            text = _mock_compress(user, aggressive=True)
        elif "judge" in sys.lower() or "score" in sys.lower():
            text = json.dumps({"score": round(0.9 + 0.1 * _seed(user), 3)})
        else:
            text = f"[mock {model} answer to: {user[:60]}...]"
        inp = sum(count_tokens(m["content"], model or "gpt-4o") for m in messages)
        return LLMResponse(text=text, input_tokens=inp,
                           output_tokens=count_tokens(text, model or "gpt-4o"),
                           live=False)

    # -- tool-calling chat (for the agentic optimiser) ----------------------
    def chat_with_tools(self, messages: list[dict], tools: list[dict],
                        model: str | None = None) -> LLMResponse:
        model = model or self.model
        if self.live:
            r = self._client.chat.completions.create(
                model=model, messages=messages, tools=tools,
                tool_choice="auto", temperature=0.2,
            )
            msg = r.choices[0].message
            calls = []
            for tc in (msg.tool_calls or []):
                calls.append({"id": tc.id, "name": tc.function.name,
                              "arguments": json.loads(tc.function.arguments)})
            return LLMResponse(text=msg.content or "", tool_calls=calls,
                               input_tokens=r.usage.prompt_tokens,
                               output_tokens=r.usage.completion_tokens, live=True)
        # ---- mock: emulate a single rewrite tool call then a final answer ----
        user = next((m["content"] for m in reversed(messages)
                     if m["role"] == "user"), "")
        msg_tokens = sum(count_tokens(str(m.get("content", "")),
                                      model or "gpt-4o") for m in messages)
        already_rewrote = any(m.get("role") == "tool" for m in messages)
        if not already_rewrote:
            calls = [{"id": "mock-1", "name": "rewrite_prompt",
                      "arguments": {"prompt": user, "strategy": "aggressive"}}]
            return LLMResponse(text="", tool_calls=calls,
                               input_tokens=msg_tokens, output_tokens=20,
                               live=False)
        # tool result already in context -> return the compressed prompt as final
        tool_out = next((m["content"] for m in messages if m.get("role") == "tool"), user)
        try:
            final = json.loads(tool_out).get("rewritten", user)
        except Exception:
            final = tool_out
        return LLMResponse(text=final, input_tokens=msg_tokens,
                           output_tokens=count_tokens(final, model or "gpt-4o"),
                           live=False)
