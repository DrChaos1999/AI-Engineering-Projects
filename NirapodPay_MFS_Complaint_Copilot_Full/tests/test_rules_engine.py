from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models import Transaction
from app.services.rules_engine import evaluate_transaction


def make_transaction(**overrides):
    values = {
        "reference_number": "TEST-001", "sender_customer_id": "S1", "sender_name": "Sender",
        "sender_phone": "01700000000", "receiver_customer_id": "R1", "receiver_name": "Receiver",
        "receiver_phone": "01800000000", "source_mfs": "A", "target_mfs": "B",
        "amount": Decimal("100.00"), "fee": Decimal("5.00"), "currency": "BDT",
        "status": "PENDING", "sender_debited": True, "receiver_credited": False,
        "reversed": False, "failure_code": None, "failure_reason": None,
        "initiated_at": datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2), "completed_at": None,
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    values.update(overrides)
    return Transaction(**values)


def test_unauthorized_is_urgent_and_routed_to_fraud():
    decision = evaluate_transaction(make_transaction(status="COMPLETED"), "I did not send this. It is unauthorized.")
    assert decision.category == "unauthorized_transfer"
    assert decision.priority == "urgent"
    assert decision.routed_team == "Fraud and Risk"
    assert decision.self_resolvable is False


def test_failed_debited_routes_to_reversal_operations():
    decision = evaluate_transaction(make_transaction(status="FAILED", failure_code="TIMEOUT"), "Money was deducted.")
    assert decision.category == "failed_debited"
    assert decision.routed_team == "Auto-Reversal Operations"


def test_reversed_can_be_self_resolvable():
    decision = evaluate_transaction(make_transaction(status="REVERSED", reversed=True), "Has my money returned?")
    assert decision.category == "reversed_transfer"
    assert decision.self_resolvable is True
