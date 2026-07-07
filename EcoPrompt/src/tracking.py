"""Experiment tracking. Uses MLflow when installed, else logs rows to CSV.

The MLflow path logs one run per (prompt, technique, downstream_model) cell with
params + metrics, under a single named experiment. View with `mlflow ui`.
The CSV path writes the identical schema to artifacts/runs.csv so analysis and
plotting work without MLflow installed.
"""
from __future__ import annotations
import csv
import os
from pathlib import Path

from .config import load_config

try:
    import mlflow  # type: ignore
    _HAS_MLFLOW = True
except Exception:  # pragma: no cover
    mlflow = None
    _HAS_MLFLOW = False

_ROOT = Path(__file__).resolve().parents[1]


class Tracker:
    def __init__(self, cfg: dict | None = None, use_mlflow: bool | None = None):
        self.cfg = cfg or load_config()
        self.use_mlflow = _HAS_MLFLOW if use_mlflow is None else use_mlflow
        self._rows: list[dict] = []
        if self.use_mlflow and _HAS_MLFLOW:
            mlflow.set_tracking_uri(self.cfg["mlflow"]["tracking_uri"])
            mlflow.set_experiment(self.cfg["mlflow"]["experiment_name"])

    def log_cell(self, params: dict, metrics: dict):
        row = {**params, **metrics}
        self._rows.append(row)
        if self.use_mlflow and _HAS_MLFLOW:
            run_name = f"{params['technique']}|{params['downstream_model']}|{params['prompt_id']}"
            with mlflow.start_run(run_name=run_name):
                mlflow.log_params(params)
                mlflow.log_metrics({k: float(v) for k, v in metrics.items()})

    def to_csv(self, path: str | None = None) -> str:
        path = path or str(_ROOT / "artifacts" / "runs.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not self._rows:
            return path
        keys = list(self._rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(self._rows)
        return path

    @property
    def backend(self) -> str:
        return "mlflow" if (self.use_mlflow and _HAS_MLFLOW) else "csv"
