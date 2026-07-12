import json
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import AuditLog, ComplaintCase, Transaction
from app.schemas import ComplaintResult, KnowledgeHit
from app.services.llm_service import LLMService
from app.services.rules_engine import evaluate_transaction
from app.services.transaction_service import (
    get_verified_transaction,
    sanitized_transaction_context,
    to_public_transaction,
)
from app.services.vector_store import PseudoVectorStore


class ComplaintOrchestrator:
    def __init__(self) -> None:
        settings = get_settings()
        knowledge_path = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.json"
        self.vector_store = PseudoVectorStore.from_json(knowledge_path)
        self.llm_service = LLMService()
        self.max_kb_results = settings.max_kb_results

    def analyze_and_create_case(
        self,
        db: Session,
        reference_number: str,
        verification_code: str,
        customer_message: str,
    ) -> ComplaintResult:
        transaction = get_verified_transaction(db, reference_number, verification_code)
        rule_decision = evaluate_transaction(transaction, customer_message)

        retrieval_query = " ".join([
            customer_message,
            rule_decision.category,
            transaction.status,
            "cross mfs" if transaction.source_mfs != transaction.target_mfs else "same mfs",
            transaction.failure_reason or "",
        ])
        knowledge_hits = self.vector_store.search(
            retrieval_query,
            top_k=self.max_kb_results,
            category=rule_decision.category,
        )
        assessment = self.llm_service.assess(
            customer_message=customer_message,
            transaction_context=sanitized_transaction_context(transaction),
            rule_decision=rule_decision,
            knowledge_hits=knowledge_hits,
        )
        case = self._create_case(db, transaction, customer_message, assessment, knowledge_hits)

        return ComplaintResult(
            case_id=case.public_case_id,
            case_status=case.status,
            transaction=to_public_transaction(transaction),
            assessment=assessment,
            knowledge_hits=knowledge_hits,
        )

    @staticmethod
    def _create_case(
        db: Session,
        transaction: Transaction,
        customer_message: str,
        assessment,
        knowledge_hits: list[KnowledgeHit],
    ) -> ComplaintCase:
        case = ComplaintCase(
            public_case_id=f"CMP-{uuid.uuid4().hex[:10].upper()}",
            transaction_id=transaction.id,
            customer_message=customer_message,
            category=assessment.category,
            priority=assessment.priority,
            routed_team=assessment.routed_team,
            summary=assessment.summary,
            initial_response=assessment.initial_response,
            next_steps_json=json.dumps(assessment.next_steps),
            cited_articles_json=json.dumps(assessment.cited_article_ids),
            status="RESOLVED_BY_BOT" if assessment.self_resolvable else "OPEN",
            self_resolvable=assessment.self_resolvable,
        )
        db.add(case)
        db.flush()
        db.add(AuditLog(
            complaint_case_id=case.id,
            event_type="CASE_CREATED",
            actor="complaint_orchestrator",
            details_json=json.dumps({
                "category": assessment.category,
                "priority": assessment.priority,
                "routed_team": assessment.routed_team,
                "status": case.status,
                "knowledge_hits": [hit.article_id for hit in knowledge_hits],
            }),
        ))
        db.commit()
        db.refresh(case)
        return case


def list_cases(db: Session) -> list[ComplaintCase]:
    return list(db.scalars(select(ComplaintCase).order_by(ComplaintCase.created_at.desc()).limit(100)))
