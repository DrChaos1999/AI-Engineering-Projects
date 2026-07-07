"""Run the full benchmark grid: prompts x techniques x downstream models.

For every cell we record:
  - original / optimized token counts and reduction %
  - optimiser token overhead (cost of doing the compression itself)
  - estimated energy (Wh) before vs after, and energy reduction %
  - estimated cost (USD) before vs after
  - quality-preservation score (0..1)
  - estimated CO2e (g) saved

Output tokens are held at config.assumed_output_tokens across techniques: the
user asked for the same deliverable, so the ANSWER length should not change --
only the INPUT prompt is compressed. This isolates the effect we care about.
"""
from __future__ import annotations
import json
from pathlib import Path

from .config import load_config
from .optimizer import optimize
from .evaluator import judge_quality
from .energy_model import estimate_energy, estimate_cost_usd
from .tracking import Tracker

_ROOT = Path(__file__).resolve().parents[1]


def load_prompts(path: str | None = None) -> list[dict]:
    path = path or str(_ROOT / "data" / "prompts.jsonl")
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run(cfg: dict | None = None, judge: bool = True,
        use_mlflow: bool | None = None) -> Tracker:
    cfg = cfg or load_config()
    prompts = load_prompts()
    tracker = Tracker(cfg, use_mlflow=use_mlflow)
    out_tok = cfg["assumed_output_tokens"]

    for p in prompts:
        for model in cfg["benchmark_models"]:
            for tech in cfg["techniques"]:
                r = optimize(p["prompt"], tech, model, cfg)

                e_before = estimate_energy(r.original_tokens, out_tok, model, cfg)
                e_after = estimate_energy(r.optimized_tokens, out_tok, model, cfg)
                # energy spent compressing (charged to the optimiser model)
                opt_model = cfg["optimizer_model"]
                e_opt = estimate_energy(r.optimizer_input_tokens,
                                        r.optimizer_output_tokens, opt_model, cfg)

                cost_before = estimate_cost_usd(r.original_tokens, out_tok, model, cfg)
                cost_after = estimate_cost_usd(r.optimized_tokens, out_tok, model, cfg)

                q = judge_quality(p["prompt"], r.optimized_prompt, model, cfg) \
                    if (judge and tech != "baseline") else 1.0

                energy_saved = e_before.energy_wh - e_after.energy_wh
                energy_red_pct = (100.0 * energy_saved / e_before.energy_wh
                                  if e_before.energy_wh else 0.0)

                params = {
                    "prompt_id": p["id"],
                    "category": p.get("category", "general"),
                    "technique": tech,
                    "downstream_model": model,
                    "optimizer_model": opt_model,
                    "live": r.live,
                }
                metrics = {
                    "orig_tokens": r.original_tokens,
                    "opt_tokens": r.optimized_tokens,
                    "tokens_saved": r.tokens_saved,
                    "token_reduction_pct": round(r.reduction_pct, 3),
                    "optimizer_overhead_tokens": r.optimizer_input_tokens + r.optimizer_output_tokens,
                    "energy_wh_before": e_before.energy_wh,
                    "energy_wh_after": e_after.energy_wh,
                    "energy_wh_optimizer": e_opt.energy_wh,
                    "energy_saved_wh": energy_saved,
                    "energy_reduction_pct": round(energy_red_pct, 3),
                    "cost_usd_before": cost_before,
                    "cost_usd_after": cost_after,
                    "cost_saved_usd": cost_before - cost_after,
                    "gco2e_saved": e_before.gco2e - e_after.gco2e,
                    "quality_score": q,
                }
                tracker.log_cell(params, metrics)
    return tracker
