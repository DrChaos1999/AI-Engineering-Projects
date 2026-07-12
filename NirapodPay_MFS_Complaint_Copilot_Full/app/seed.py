from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Transaction


def seed_database(db: Session) -> None:
    count = db.scalar(select(func.count()).select_from(Transaction))
    if count and count > 0:
        return

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [
        dict(reference_number="MFS202607120001", sender_customer_id="CUS-1001", sender_name="Amina Rahman", sender_phone="+8801712344488", receiver_customer_id="CUS-2001", receiver_name="Karim Hasan", receiver_phone="+8801811112233", source_mfs="NirapodPay", target_mfs="NirapodPay", amount=Decimal("2500.00"), fee=Decimal("5.00"), currency="BDT", status="COMPLETED", sender_debited=True, receiver_credited=True, reversed=False, failure_code=None, failure_reason=None, initiated_at=now-timedelta(hours=2), completed_at=now-timedelta(hours=1, minutes=59)),
        dict(reference_number="MFS202607120002", sender_customer_id="CUS-1002", sender_name="Nadia Sultana", sender_phone="+8801912347712", receiver_customer_id="CUS-2002", receiver_name="Rafi Ahmed", receiver_phone="+8801611223344", source_mfs="NirapodPay", target_mfs="NirapodPay", amount=Decimal("1250.00"), fee=Decimal("5.00"), currency="BDT", status="FAILED", sender_debited=True, receiver_credited=False, reversed=False, failure_code="SWITCH_TIMEOUT", failure_reason="No final switch acknowledgement before timeout.", initiated_at=now-timedelta(hours=5), completed_at=None),
        dict(reference_number="MFS202607120003", sender_customer_id="CUS-1003", sender_name="Sabbir Hossain", sender_phone="+8801512340091", receiver_customer_id="CUS-2003", receiver_name="Maya Islam", receiver_phone="+8801711220099", source_mfs="NirapodPay", target_mfs="NirapodPay", amount=Decimal("800.00"), fee=Decimal("5.00"), currency="BDT", status="REVERSED", sender_debited=True, receiver_credited=False, reversed=True, failure_code="BENEFICIARY_UNAVAILABLE", failure_reason="Beneficiary wallet was temporarily unavailable.", initiated_at=now-timedelta(days=1), completed_at=now-timedelta(hours=23)),
        dict(reference_number="MFS202607120004", sender_customer_id="CUS-1004", sender_name="Tania Akter", sender_phone="+8801312343410", receiver_customer_id="CUS-2004", receiver_name="Imran Kabir", receiver_phone="+8801812121212", source_mfs="NirapodPay", target_mfs="ShurokkhaCash", amount=Decimal("5000.00"), fee=Decimal("10.00"), currency="BDT", status="PENDING", sender_debited=True, receiver_credited=False, reversed=False, failure_code=None, failure_reason=None, initiated_at=now-timedelta(hours=3), completed_at=None),
        dict(reference_number="MFS202607120005", sender_customer_id="CUS-1005", sender_name="Farhana Yasmin", sender_phone="+8801812348824", receiver_customer_id="CUS-2005", receiver_name="Shakil Mia", receiver_phone="+8801719191919", source_mfs="NirapodPay", target_mfs="ShurokkhaCash", amount=Decimal("3200.00"), fee=Decimal("10.00"), currency="BDT", status="COMPLETED", sender_debited=True, receiver_credited=False, reversed=False, failure_code=None, failure_reason=None, initiated_at=now-timedelta(hours=7), completed_at=now-timedelta(hours=6, minutes=58)),
        dict(reference_number="MFS202607120006", sender_customer_id="CUS-1006", sender_name="Rashed Chowdhury", sender_phone="+8801712346620", receiver_customer_id="CUS-2006", receiver_name="Unknown Merchant", receiver_phone="+8801999999999", source_mfs="NirapodPay", target_mfs="ShurokkhaCash", amount=Decimal("9800.00"), fee=Decimal("10.00"), currency="BDT", status="COMPLETED", sender_debited=True, receiver_credited=True, reversed=False, failure_code=None, failure_reason=None, initiated_at=now-timedelta(minutes=40), completed_at=now-timedelta(minutes=39)),
    ]
    db.add_all([Transaction(**row) for row in rows])
    db.commit()
