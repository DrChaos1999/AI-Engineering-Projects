"""Scale the (small) per-query savings to production call volume.

A single compressed prompt saves little. But a system prompt / RAG template /
few-shot block is sent on EVERY call. Compress it once, save on every request.
This module projects daily/annual energy, cost and CO2e savings for a given
calls-per-day, and is what turns "0.3% per query" into a headline number.
"""
from __future__ import annotations
import pandas as pd


def project_savings(csv_path: str, calls_per_day: int = 1_000_000,
                    technique: str = "agentic",
                    category: str | None = "system",
                    downstream_model: str = "gpt-4o") -> dict:
    df = pd.read_csv(csv_path)
    sel = df[(df.technique == technique) &
             (df.downstream_model == downstream_model)]
    if category:
        sel = sel[sel.category == category]
    if sel.empty:
        raise ValueError("no rows match that selection")

    wh_per_call = sel["energy_saved_wh"].mean()
    usd_per_call = sel["cost_saved_usd"].mean()
    g_per_call = sel["gco2e_saved"].mean()
    tok_per_call = sel["tokens_saved"].mean()

    days = 365
    return {
        "selection": f"{technique} / {category or 'all'} / {downstream_model}",
        "calls_per_day": calls_per_day,
        "tokens_saved_per_call": round(tok_per_call, 2),
        "energy_saved_kwh_per_day": wh_per_call * calls_per_day / 1000.0,
        "energy_saved_kwh_per_year": wh_per_call * calls_per_day * days / 1000.0,
        "cost_saved_usd_per_day": usd_per_call * calls_per_day,
        "cost_saved_usd_per_year": usd_per_call * calls_per_day * days,
        "co2e_kg_per_year": g_per_call * calls_per_day * days / 1000.0,
    }


def projection_table(csv_path: str,
                     volumes=(10_000, 100_000, 1_000_000, 10_000_000)) -> pd.DataFrame:
    rows = []
    for v in volumes:
        p = project_savings(csv_path, calls_per_day=v)
        rows.append({
            "calls_per_day": f"{v:,}",
            "kWh_saved_per_year": round(p["energy_saved_kwh_per_year"], 1),
            "USD_saved_per_year": round(p["cost_saved_usd_per_year"], 0),
            "tCO2e_saved_per_year": round(p["co2e_kg_per_year"] / 1000.0, 3),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    csv = sys.argv[1] if len(sys.argv) > 1 else \
        str(Path(__file__).resolve().parents[1] / "artifacts" / "runs.csv")
    print("Projected annual savings (compressing a reused system prompt, gpt-4o):\n")
    print(projection_table(csv).to_string(index=False))
