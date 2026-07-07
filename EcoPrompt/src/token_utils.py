"""Exact token counting via tiktoken, with a flagged offline fallback.

Tokens are the *measured ground truth* of this whole project, so we want the
real tokeniser whenever it is installed. When it is not (e.g. an air-gapped
demo box) we fall back to a coarse char-based heuristic and SHOUT about it so
nobody mistakes the estimate for a measurement.
"""
from __future__ import annotations
import math
import warnings
from functools import lru_cache

from .config import load_config, model_cfg

try:
    import tiktoken  # type: ignore
    _HAS_TIKTOKEN = True
except Exception:  # pragma: no cover - depends on environment
    tiktoken = None
    _HAS_TIKTOKEN = False
    warnings.warn(
        "tiktoken not installed -> using APPROXIMATE char/4 token counts. "
        "Install tiktoken for exact, ground-truth counts.",
        RuntimeWarning,
    )


@lru_cache(maxsize=8)
def _encoder(encoding: str):
    if not _HAS_TIKTOKEN:
        return None
    try:
        return tiktoken.get_encoding(encoding)
    except Exception:
        return tiktoken.get_encoding("cl100k_base")


def _encoding_for(model: str) -> str:
    try:
        return model_cfg(model)["encoding"]
    except Exception:
        return load_config().get("default_encoding", "o200k_base")


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Return token count for `text` under `model`'s tokeniser.

    Exact when tiktoken is present; otherwise an explicit approximation.
    """
    if not text:
        return 0
    enc = _encoder(_encoding_for(model))
    if enc is not None:
        return len(enc.encode(text))
    # Fallback heuristic: GPT BPE averages ~4 chars/token for English prose.
    return max(1, math.ceil(len(text) / 4))


def is_exact() -> bool:
    """True if counts come from the real tokeniser."""
    return _HAS_TIKTOKEN
