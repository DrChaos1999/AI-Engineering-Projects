"""Sanity tests for the energy model. Run: python -m pytest tests/"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.energy_model import estimate_energy, estimate_cost_usd
from src.token_utils import count_tokens


def test_energy_monotonic_in_tokens():
    a = estimate_energy(100, 100, "gpt-4o")
    b = estimate_energy(200, 100, "gpt-4o")
    assert b.energy_wh > a.energy_wh


def test_decode_more_expensive_than_prefill_per_token():
    # equal token counts: decode joules should exceed prefill joules
    r = estimate_energy(100, 100, "gpt-4o")
    assert r.decode_joules > r.prefill_joules


def test_bigger_model_more_energy():
    big = estimate_energy(100, 100, "gpt-4o")
    small = estimate_energy(100, 100, "gpt-4o-mini")
    assert big.energy_wh > small.energy_wh


def test_cost_positive():
    assert estimate_cost_usd(1000, 500, "gpt-4o") > 0


def test_token_count_nonneg():
    assert count_tokens("") == 0
    assert count_tokens("hello world") >= 1
