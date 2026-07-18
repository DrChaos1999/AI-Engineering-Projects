import pytest

from config import parse_customer_plans


def test_parse_customer_plans():
    plans = parse_customer_plans("five:5:3, ten:10:0")
    assert plans["five"].minutes == 5
    assert plans["five"].max_questions == 3
    assert plans["ten"].minutes == 10
    assert plans["ten"].max_questions == 0


def test_invalid_customer_plan_rejected():
    with pytest.raises(RuntimeError):
        parse_customer_plans("broken:five:3")
