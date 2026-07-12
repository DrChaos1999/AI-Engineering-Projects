from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

ComplaintCategory = Literal[
    "pending_transfer", "failed_debited", "receiver_not_credited",
    "reversed_transfer", "duplicate_transfer", "wrong_receiver",
    "unauthorized_transfer", "fee_or_amount_dispute", "unknown",
]
Priority = Literal["low", "medium", "high", "urgent"]


class ComplaintRequest(BaseModel):
    reference_number: str = Field(..., min_length=8, max_length=64)
    verification_code: str = Field(..., min_length=4, max_length=12)
    message: str = Field(..., min_length=5, max_length=2000)


class TransactionPublic(BaseModel):
    reference_number: str
    sender: str
    receiver: str
    source_mfs: str
    target_mfs: str
    amount: Decimal
    fee: Decimal
    currency: str
    status: str
    sender_debited: bool
    receiver_credited: bool
    reversed: bool
    initiated_at: datetime
    completed_at: datetime | None


class KnowledgeHit(BaseModel):
    article_id: str
    title: str
    category: str
    score: float
    resolution: str


class RuleDecision(BaseModel):
    category: ComplaintCategory
    priority: Priority
    routed_team: str
    self_resolvable: bool
    safe_initial_response: str
    required_actions: list[str]
    reason_codes: list[str]


class ComplaintAssessment(BaseModel):
    category: ComplaintCategory
    priority: Priority
    summary: str = Field(..., min_length=20, max_length=800)
    initial_response: str = Field(..., min_length=20, max_length=1500)
    routed_team: str
    self_resolvable: bool
    next_steps: list[str] = Field(..., min_length=1, max_length=8)
    cited_article_ids: list[str] = Field(default_factory=list, max_length=5)
    confidence: float = Field(..., ge=0, le=1)


class ComplaintResult(BaseModel):
    case_id: str
    case_status: str
    transaction: TransactionPublic
    assessment: ComplaintAssessment
    knowledge_hits: list[KnowledgeHit]


class DemoReference(BaseModel):
    reference_number: str
    verification_code: str
    scenario: str


class CaseListItem(BaseModel):
    case_id: str
    reference_number: str
    category: str
    priority: str
    routed_team: str
    summary: str
    status: str
    created_at: datetime
