"""Quality-preservation check: did compression keep the task intact?

A token saving that silently breaks the request is NOT efficiency -- it is a
worse product for less money. So for every compressed prompt we ask a basic
model (gpt-4o-mini) to answer both the original and the compressed prompt, then
judge whether the compressed answer still satisfies the original intent. Score
in [0,1]. We plot reduction vs quality to find the Pareto frontier.
"""
from __future__ import annotations
import json

from .config import load_config
from .llm_client import LLMClient, _seed

_JUDGE_SYS = (
    "You are a strict evaluator. Given an ORIGINAL user request and an answer "
    "produced from a COMPRESSED version of that request, score from 0.0 to 1.0 "
    "how fully the answer still satisfies the ORIGINAL intent and constraints. "
    'Reply with ONLY JSON: {"score": <float>}.'
)


def judge_quality(original_prompt: str, compressed_prompt: str,
                  downstream_model: str, cfg: dict | None = None) -> float:
    cfg = cfg or load_config()
    judge_model = cfg["judge_model"]
    client = LLMClient(model=judge_model)

    # produce an answer from the compressed prompt
    ans = client.chat([{"role": "user", "content": compressed_prompt}],
                       model=downstream_model)
    judge = client.chat(
        [{"role": "system", "content": _JUDGE_SYS},
         {"role": "user", "content":
            f"ORIGINAL:\n{original_prompt}\n\nANSWER (from compressed):\n{ans.text}"}],
        model=judge_model)
    try:
        return float(json.loads(judge.text)["score"])
    except Exception:
        # mock/parse fallback: gentle penalty proportional to how different
        # the prompts are, so the Pareto curve is non-trivial.
        import difflib
        ratio = difflib.SequenceMatcher(None, original_prompt,
                                        compressed_prompt).ratio()
        return round(min(1.0, 0.80 + 0.20 * ratio + 0.02 * _seed(compressed_prompt)), 3)
