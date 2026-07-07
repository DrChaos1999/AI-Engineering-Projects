"""Prompt-optimisation techniques benchmarked against each other.

baseline     : control, returns the prompt unchanged (0 optimiser cost).
rule_based   : deterministic regex stripping of politeness/filler. 0 LLM cost.
llm_rewrite  : one-shot rewrite by a basic model (gpt-4o-mini) for brevity.
agentic      : a tool-using loop where a basic model rewrites, counts tokens
               via a tool, checks the reduction, and retries if needed.

Each returns an OptimizationResult capturing the compressed prompt AND the
optimiser's own token overhead (compressing costs tokens too -- a fair
accounting must include it, otherwise "savings" can be illusory at low reuse).
"""
from __future__ import annotations
from dataclasses import dataclass

from .config import load_config
from .llm_client import LLMClient, _mock_compress, _light_compress
from .tools import TOOL_SCHEMAS, dispatch
from .token_utils import count_tokens

_REWRITE_SYS = (
    "You rewrite user prompts to use as few tokens as possible while fully "
    "preserving the task and any hard constraints. Remove politeness, filler, "
    "and redundancy. Keep all task-relevant nouns. Reply with ONLY the rewritten "
    "prompt, no preamble."
)
_REWRITE_SYS_AGG = _REWRITE_SYS + " Be aggressive: telegraphic style is fine."

_AGENT_SYS = (
    "You are a prompt-efficiency agent. Goal: minimise the token count of the "
    "user's prompt without losing intent. Use rewrite_prompt to compress, then "
    "count_tokens to verify. If the rewrite still looks bloated, rewrite again "
    "more aggressively. When satisfied, reply with ONLY the final compressed prompt."
)


@dataclass
class OptimizationResult:
    technique: str
    original_prompt: str
    optimized_prompt: str
    original_tokens: int
    optimized_tokens: int
    optimizer_input_tokens: int   # tokens spent BY the optimiser model
    optimizer_output_tokens: int
    live: bool

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.optimized_tokens

    @property
    def reduction_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 100.0 * self.tokens_saved / self.original_tokens


def _count(prompt: str, model: str) -> int:
    return count_tokens(prompt, model)


def optimize(prompt: str, technique: str, downstream_model: str,
             cfg: dict | None = None) -> OptimizationResult:
    cfg = cfg or load_config()
    opt_model = cfg["optimizer_model"]
    orig_tokens = _count(prompt, downstream_model)

    if technique == "baseline":
        return OptimizationResult(
            technique, prompt, prompt, orig_tokens, orig_tokens, 0, 0, live=False)

    if technique == "rule_based":
        new = _light_compress(prompt)
        return OptimizationResult(
            technique, prompt, new, orig_tokens, _count(new, downstream_model),
            0, 0, live=False)

    client = LLMClient(model=opt_model)

    if technique == "llm_rewrite":
        resp = client.chat(
            [{"role": "system", "content": _REWRITE_SYS},
             {"role": "user", "content": prompt}], model=opt_model)
        new = resp.text.strip() or prompt
        return OptimizationResult(
            technique, prompt, new, orig_tokens, _count(new, downstream_model),
            resp.input_tokens, resp.output_tokens, live=resp.live)

    if technique == "agentic":
        return _agentic_optimize(client, prompt, downstream_model, opt_model,
                                 orig_tokens)

    raise ValueError(f"unknown technique: {technique}")


def _agentic_optimize(client: LLMClient, prompt: str, downstream_model: str,
                      opt_model: str, orig_tokens: int,
                      max_turns: int = 4) -> OptimizationResult:
    messages = [{"role": "system", "content": _AGENT_SYS},
                {"role": "user", "content": prompt}]
    opt_in = opt_out = 0
    final = prompt
    for _ in range(max_turns):
        resp = client.chat_with_tools(messages, TOOL_SCHEMAS, model=opt_model)
        opt_in += resp.input_tokens
        opt_out += resp.output_tokens
        if resp.tool_calls:
            # record assistant tool-call turn, then execute + feed results back
            messages.append({"role": "assistant", "content": resp.text or "",
                             "tool_calls": [
                                 {"id": c["id"], "type": "function",
                                  "function": {"name": c["name"],
                                               "arguments": _json(c["arguments"])}}
                                 for c in resp.tool_calls]})
            for c in resp.tool_calls:
                out = dispatch(c["name"], c["arguments"])
                messages.append({"role": "tool", "tool_call_id": c["id"],
                                 "content": out})
            continue
        if resp.text:
            final = resp.text.strip()
            break
    return OptimizationResult(
        "agentic", prompt, final, orig_tokens, _count(final, downstream_model),
        opt_in, opt_out, live=client.live)


def _json(obj) -> str:
    import json
    return json.dumps(obj)
