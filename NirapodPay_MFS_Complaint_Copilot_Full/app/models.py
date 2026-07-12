from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    sender_customer_id: Mapped[str] = mapped_column(String(64), index=True)
    sender_name: Mapped[str] = mapped_column(String(120))
    sender_phone: Mapped[str] = mapped_column(String(32))
    receiver_customer_id: Mapped[str] = mapped_column(String(64), index=True)
    receiver_name: Mapped[str] = mapped_column(String(120))
    receiver_phone: Mapped[str] = mapped_column(String(32))
    source_mfs: Mapped[str] = mapped_column(String(64))
    target_mfs: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(8), default="BDT")
    status: Mapped[str] = mapped_column(String(32), index=True)
    sender_debited: Mapped[bool] = mapped_column(Boolean, default=False)
    receiver_credited: Mapped[bool] = mapped_column(Boolean, default=False)
    reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    initiated_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    complaints: Mapped[list["ComplaintCase"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")


class ComplaintCase(Base):
    __tablename__ = "complaint_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    customer_message: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(16), index=True)
    routed_team: Mapped[str] = mapped_column(String(120), index=True)
    summary: Mapped[str] = mapped_column(Text)
    initial_response: Mapped[str] = mapped_column(Text)
    next_steps_json: Mapped[str] = mapped_column(Text)
    cited_articles_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    self_resolvable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transaction: Mapped[Transaction] = relationship(back_populates="complaints")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="complaint_case", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_case_id: Mapped[int] = mapped_column(ForeignKey("complaint_cases.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(64))
    details_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    complaint_case: Mapped[ComplaintCase] = relationship(back_populates="audit_logs")
