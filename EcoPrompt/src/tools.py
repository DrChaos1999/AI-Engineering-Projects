"""Custom tools the agentic optimiser can call.

Each tool is (a) a real Python function and (b) an OpenAI function-calling JSON
schema. The agent (a *basic* model, gpt-4o-mini) decides when to call them:
it rewrites a prompt, counts the result, checks the energy saving, and retries
if it overshot or undershot. This is the "clearly defined custom tools that use
agentic AI by using basic models" part of the brief.
"""
from __future__ import annotations
import json

from .token_utils import count_tokens
from .energy_model import estimate_energy
from .llm_client import _mock_compress


# --- tool implementations --------------------------------------------------
def tool_count_tokens(text: str, model: str = "gpt-4o") -> dict:
    return {"tokens": count_tokens(text, model)}


def tool_estimate_energy(input_tokens: int, output_tokens: int,
                         model: str = "gpt-4o") -> dict:
    r = estimate_energy(input_tokens, output_tokens, model)
    return {"energy_wh": round(r.energy_wh, 6),
            "prefill_joules": round(r.prefill_joules, 3),
            "decode_joules": round(r.decode_joules, 3)}


def tool_rewrite_prompt(prompt: str, strategy: str = "concise") -> dict:
    """Mock/standalone rewrite. In live mode the model rewrites directly,
    but exposing this as a tool lets the agent self-correct deterministically."""
    rewritten = _mock_compress(prompt, aggressive=(strategy == "aggressive"))
    return {"rewritten": rewritten,
            "tokens_before": count_tokens(prompt),
            "tokens_after": count_tokens(rewritten)}


TOOL_IMPLS = {
    "count_tokens": tool_count_tokens,
    "estimate_energy": tool_estimate_energy,
    "rewrite_prompt": tool_rewrite_prompt,
}


# --- OpenAI tool schemas ---------------------------------------------------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "count_tokens",
            "description": "Count tokens of a text for a given model's tokeniser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "model": {"type": "string", "default": "gpt-4o"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_energy",
            "description": "Estimate inference energy (Wh) for given token counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_tokens": {"type": "integer"},
                    "output_tokens": {"type": "integer"},
                    "model": {"type": "string", "default": "gpt-4o"},
                },
                "required": ["input_tokens", "output_tokens"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rewrite_prompt",
            "description": ("Rewrite a prompt to use fewer tokens while preserving "
                            "the user's intent. strategy: 'concise' or 'aggressive'."),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "strategy": {"type": "string", "enum": ["concise", "aggressive"]},
                },
                "required": ["prompt"],
            },
        },
    },
]


def dispatch(name: str, arguments: dict) -> str:
    """Run a tool by name; return JSON string (what the model receives back)."""
    if name not in TOOL_IMPLS:
        return json.dumps({"error": f"unknown tool {name}"})
    return json.dumps(TOOL_IMPLS[name](**arguments))
