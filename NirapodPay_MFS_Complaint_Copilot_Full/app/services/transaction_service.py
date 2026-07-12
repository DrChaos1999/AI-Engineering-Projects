from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Transaction
from app.schemas import TransactionPublic
from app.services.masking import mask_name, mask_phone


class TransactionNotFoundError(Exception):
    pass


class VerificationFailedError(Exception):
    pass


def get_verified_transaction(db: Session, reference_number: str, verification_code: str) -> Transaction:
    transaction = db.scalar(
        select(Transaction).where(Transaction.reference_number == reference_number.strip().upper())
    )
    if transaction is None:
        raise TransactionNotFoundError("No transaction was found for that reference.")

    expected = "".join(character for character in transaction.sender_phone if character.isdigit())[-4:]
    if verification_code.strip() != expected:
        raise VerificationFailedError("Customer verification failed.")
    return transaction


def to_public_transaction(transaction: Transaction) -> TransactionPublic:
    return TransactionPublic(
        reference_number=transaction.reference_number,
        sender=f"{mask_name(transaction.sender_name)} ({mask_phone(transaction.sender_phone)})",
        receiver=f"{mask_name(transaction.receiver_name)} ({mask_phone(transaction.receiver_phone)})",
        source_mfs=transaction.source_mfs,
        target_mfs=transaction.target_mfs,
        amount=transaction.amount,
        fee=transaction.fee,
        currency=transaction.currency,
        status=transaction.status,
        sender_debited=transaction.sender_debited,
        receiver_credited=transaction.receiver_credited,
        reversed=transaction.reversed,
        initiated_at=transaction.initiated_at,
        completed_at=transaction.completed_at,
    )


def sanitized_transaction_context(transaction: Transaction) -> dict:
    return {
        "reference_number": transaction.reference_number,
        "source_mfs": transaction.source_mfs,
        "target_mfs": transaction.target_mfs,
        "amount": float(transaction.amount),
        "fee": float(transaction.fee),
        "currency": transaction.currency,
        "status": transaction.status,
        "sender_debited": transaction.sender_debited,
        "receiver_credited": transaction.receiver_credited,
        "reversed": transaction.reversed,
        "failure_code": transaction.failure_code,
        "failure_reason": transaction.failure_reason,
        "initiated_at": transaction.initiated_at.isoformat(),
        "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
        "is_cross_mfs": transaction.source_mfs != transaction.target_mfs,
    }
