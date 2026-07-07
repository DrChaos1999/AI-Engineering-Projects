"""Transparent FLOPs -> energy model for transformer inference.

WHY A MODEL AND NOT A MEASUREMENT
---------------------------------
OpenAI does not expose per-request energy. We therefore estimate it from the
one thing we *can* measure exactly -- token counts -- using first-principles
transformer arithmetic. Every assumption is a named constant in config.yaml so
the estimate is auditable and tunable, never a magic number.

THE MODEL
---------
A forward pass over one token costs ~ `2 * N` FLOPs, where N is the number of
parameters active for that token (the 2 = one multiply + one add per weight).

We split the work into two regimes because they have very different hardware
efficiency:

  * PREFILL  -- reading the input prompt. All input tokens are processed in
    one big parallel matmul, so the accelerator runs near peak utilisation
    (high MFU). FLOPs ~= 2 * N * input_tokens.

  * DECODE   -- generating the answer one token at a time. Each step is a tall,
    skinny matmul that is memory-bandwidth bound, so utilisation is low
    (MFU maybe 3-10%). FLOPs ~= 2 * N * output_tokens, but each FLOP costs
    far more energy than in prefill.

Energy(J) = FLOPs / (peak_flops * MFU) * board_power, summed over both regimes,
then multiplied by PUE (datacentre overhead). We report Wh (J / 3600).

KEY CONSEQUENCE FOR THIS PROJECT
--------------------------------
Because decode is ~ (prefill_mfu / decode_mfu) times less efficient per token,
the *output* usually dominates energy. Compressing a short prompt barely moves
the needle; compressing a long, frequently-reused input (system prompt, RAG
context, few-shot block) is where energy is actually saved. The model makes
this visible instead of hiding it.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

from .config import load_config, model_cfg


@dataclass
class EnergyResult:
    input_tokens: int
    output_tokens: int
    prefill_joules: float
    decode_joules: float
    total_joules: float
    energy_wh: float
    energy_kwh: float
    gco2e: float

    def as_dict(self) -> dict:
        return asdict(self)


def estimate_energy(
    input_tokens: int,
    output_tokens: int,
    model: str,
    cfg: dict | None = None,
) -> EnergyResult:
    cfg = cfg or load_config()
    e = cfg["energy"]
    N = float(model_cfg(model, cfg)["effective_active_params"])

    flops_per_tok = e["flops_per_token_per_param"] * N  # ~2N
    peak = e["gpu_peak_flops"]
    power = e["gpu_power_watts"]
    pue = e["pue"]

    # Effective FLOP/s in each regime = peak * utilisation.
    prefill_flops_s = peak * e["prefill_mfu"]
    decode_flops_s = peak * e["decode_mfu"]

    # Joules = (FLOPs / FLOP_per_s) seconds * Watts.
    prefill_j = (flops_per_tok * input_tokens) / prefill_flops_s * power * pue
    decode_j = (flops_per_tok * output_tokens) / decode_flops_s * power * pue
    total_j = prefill_j + decode_j

    wh = total_j / 3600.0
    kwh = wh / 1000.0
    gco2e = kwh * cfg.get("carbon", {}).get("grid_gco2e_per_kwh", 0.0)

    return EnergyResult(
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
        prefill_joules=prefill_j,
        decode_joules=decode_j,
        total_joules=total_j,
        energy_wh=wh,
        energy_kwh=kwh,
        gco2e=gco2e,
    )


def estimate_cost_usd(input_tokens: int, output_tokens: int, model: str,
                      cfg: dict | None = None) -> float:
    cfg = cfg or load_config()
    m = model_cfg(model, cfg)
    return (input_tokens * m["price_in"] + output_tokens * m["price_out"]) / 1e6
