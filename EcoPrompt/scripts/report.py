#!/usr/bin/env python3
"""Generate statistical tables + comparison plots from artifacts/runs.csv."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import stats as S

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def _bar(ax, labels, values, errs=None, title="", ylabel="", color="#2e7d32"):
    x = np.arange(len(labels))
    ax.bar(x, values, yerr=errs, capsize=4, color=color, alpha=0.85,
           edgecolor="#1b3a1c")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_title(title, fontsize=11, weight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)


def main():
    csv = str(ART / "runs.csv")
    df = S.load_runs(csv)
    rep = S.full_report(csv)

    pd.set_option("display.width", 120)
    pd.set_option("display.float_format", lambda v: f"{v:,.4f}")

    print("\n=== Token reduction by technique ===")
    print(rep["by_technique"].to_string(index=False))
    print("\n=== Energy per query (Wh, baseline prompts) by downstream model ===")
    print(rep["energy_by_model"].to_string(index=False))
    print("\n=== Paired Wilcoxon vs baseline (token reduction %) ===")
    print(rep["paired_tests"].to_string(index=False))
    print("\n=== Omnibus across techniques (energy reduction %) ===")
    for k, v in rep["omnibus"].items():
        print(f"  {k}: {v:.4f}")
    print("\n=== Pareto: reduction vs quality ===")
    print(rep["pareto"].to_string(index=False))

    # ---- plots ----
    tdf = rep["by_technique"]
    fig, ax = plt.subplots(figsize=(7, 4))
    _bar(ax, tdf["technique"], tdf["token_reduction_pct_mean"],
         tdf["ci95"], "Mean token reduction by technique (95% CI)",
         "tokens saved (%)")
    fig.tight_layout(); fig.savefig(ART / "fig_token_reduction.png", dpi=140)

    edf = rep["energy_by_model"]
    fig, ax = plt.subplots(figsize=(7, 4))
    _bar(ax, edf["downstream_model"], edf["energy_wh_before_mean"] * 1000,
         None, "Estimated energy per query by model",
         "energy (mWh, modelled)", color="#1565c0")
    fig.tight_layout(); fig.savefig(ART / "fig_energy_by_model.png", dpi=140)

    pf = rep["pareto"]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(pf["token_reduction_pct"], pf["quality_score"], s=120,
               color="#6a1b9a", zorder=3)
    for _, r in pf.iterrows():
        ax.annotate(r["technique"], (r["token_reduction_pct"], r["quality_score"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.set_xlabel("token reduction (%)"); ax.set_ylabel("quality retained (0-1)")
    ax.set_title("Efficiency frontier: savings vs quality", weight="bold")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(ART / "fig_pareto.png", dpi=140)

    # category effect: short prompts vs long reusable prompts
    cat = (df[df.technique != "baseline"]
           .groupby("category")["energy_saved_wh"].mean() * 1000)
    fig, ax = plt.subplots(figsize=(7, 4))
    _bar(ax, cat.index.tolist(), cat.values, None,
         "Energy saved per query by prompt type",
         "energy saved (mWh, modelled)", color="#ef6c00")
    fig.tight_layout(); fig.savefig(ART / "fig_savings_by_category.png", dpi=140)

    print(f"\n[plots] saved 4 figures to {ART}")


if __name__ == "__main__":
    main()
