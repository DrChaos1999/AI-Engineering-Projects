"""Load and validate the YAML config."""
from __future__ import annotations
import os
from pathlib import Path
from functools import lru_cache
import yaml

_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.environ.get("ECOPROMPT_CONFIG", _ROOT / "config.yaml"))


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict:
    p = Path(path) if path else CONFIG_PATH
    with open(p, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    # yaml parses 8.0e9 as float already; just sanity-check required keys.
    for key in ("models", "energy", "techniques", "benchmark_models"):
        if key not in cfg:
            raise ValueError(f"config missing required key: {key}")
    return cfg


def model_cfg(name: str, cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    if name not in cfg["models"]:
        raise KeyError(f"unknown model '{name}'. Known: {list(cfg['models'])}")
    return cfg["models"][name]
