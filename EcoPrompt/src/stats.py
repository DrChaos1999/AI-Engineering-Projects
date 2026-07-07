"""Statistical comparison of techniques and models.

Provides:
  * per-technique and per-model aggregate tables (mean, std, n, 95% CI)
  * paired Wilcoxon signed-rank tests (each technique vs baseline, paired by
    prompt) on token reduction -- non-parametric, no normality assumption
  * one-way ANOVA + Kruskal-Wallis across techniques on energy reduction
  * a quality-vs-reduction Pareto table
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def load_runs(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def _ci95(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    if len(x) < 2:
        return 0.0
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x))


def aggregate_by(df: pd.DataFrame, by: str,
                 metric: str = "token_reduction_pct") -> pd.DataFrame:
    g = df.groupby(by)[metric]
    out = g.agg(["mean", "std", "count"]).reset_index()
    out["ci95"] = g.apply(lambda s: _ci95(s.values)).values
    out = out.rename(columns={"mean": f"{metric}_mean",
                              "std": f"{metric}_std",
                              "count": "n"})
    return out.sort_values(f"{metric}_mean", ascending=False)


def paired_vs_baseline(df: pd.DataFrame,
                       metric: str = "token_reduction_pct") -> pd.DataFrame:
    """Wilcoxon signed-rank: each technique vs baseline, paired on prompt_id
    (averaged across downstream models to get one value per prompt)."""
    rows = []
    base = (df[df.technique == "baseline"]
            .groupby("prompt_id")[metric].mean())
    for tech in df.technique.unique():
        if tech == "baseline":
            continue
        cur = (df[df.technique == tech].groupby("prompt_id")[metric].mean())
        common = base.index.intersection(cur.index)
        a, b = cur.loc[common].values, base.loc[common].values
        diff = a - b
        if np.allclose(diff, 0):
            stat, p = np.nan, 1.0
        else:
            try:
                stat, p = stats.wilcoxon(a, b)
            except ValueError:
                stat, p = np.nan, np.nan
        rows.append({"technique": tech, "n_pairs": len(common),
                     "mean_diff_vs_baseline": float(np.mean(diff)),
                     "wilcoxon_stat": stat, "p_value": p,
                     "significant_0.05": (p < 0.05) if p == p else False})
    return pd.DataFrame(rows).sort_values("mean_diff_vs_baseline", ascending=False)


def omnibus_across_techniques(df: pd.DataFrame,
                              metric: str = "energy_reduction_pct") -> dict:
    groups = [g[metric].values for _, g in df[df.technique != "baseline"]
              .groupby("technique")]
    groups = [g for g in groups if len(g) > 1]
    out = {}
    if len(groups) >= 2:
        f, p = stats.f_oneway(*groups)
        out["anova_F"], out["anova_p"] = float(f), float(p)
        h, ph = stats.kruskal(*groups)
        out["kruskal_H"], out["kruskal_p"] = float(h), float(ph)
    return out


def pareto_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per technique: mean token reduction vs mean quality retained."""
    nb = df[df.technique != "baseline"]
    g = nb.groupby("technique").agg(
        token_reduction_pct=("token_reduction_pct", "mean"),
        energy_reduction_pct=("energy_reduction_pct", "mean"),
        quality_score=("quality_score", "mean"),
        optimizer_overhead_tokens=("optimizer_overhead_tokens", "mean"),
    ).reset_index()
    # simple efficiency score: reduction weighted by quality retained
    g["quality_weighted_reduction"] = (g.token_reduction_pct * g.quality_score)
    return g.sort_values("quality_weighted_reduction", ascending=False)


def full_report(csv_path: str) -> dict:
    df = load_runs(csv_path)
    return {
        "by_technique": aggregate_by(df, "technique"),
        "by_model": aggregate_by(df, "downstream_model"),
        "energy_by_model": aggregate_by(df, "downstream_model", "energy_wh_before"),
        "paired_tests": paired_vs_baseline(df),
        "omnibus": omnibus_across_techniques(df),
        "pareto": pareto_table(df),
    }
