#!/usr/bin/env python3
"""Run the EcoPrompt benchmark and write artifacts/runs.csv (+ MLflow runs)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.experiment import run
from src.token_utils import is_exact
from src.llm_client import _HAS_OPENAI


def main():
    ap = argparse.ArgumentParser(description="Run EcoPrompt benchmark")
    ap.add_argument("--no-judge", action="store_true",
                    help="skip the LLM quality judge (faster/cheaper)")
    ap.add_argument("--no-mlflow", action="store_true",
                    help="force CSV-only tracking")
    ap.add_argument("--out", default=None, help="output CSV path")
    args = ap.parse_args()

    print(f"[env] exact tokeniser : {is_exact()}")
    print(f"[env] openai available: {_HAS_OPENAI}")
    tracker = run(judge=not args.no_judge,
                  use_mlflow=(False if args.no_mlflow else None))
    path = tracker.to_csv(args.out)
    print(f"[done] backend={tracker.backend}  rows={len(tracker._rows)}")
    print(f"[done] csv -> {path}")
    if tracker.backend == "mlflow":
        print("[hint] view runs with:  mlflow ui  (then open http://localhost:5000)")


if __name__ == "__main__":
    main()
