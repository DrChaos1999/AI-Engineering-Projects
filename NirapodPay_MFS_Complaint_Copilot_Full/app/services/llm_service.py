import json
from typing import Any
from app.config import get_settings
from app.schemas import ComplaintAssessment, KnowledgeHit, RuleDecision

SYSTEM_PROMPT = """
You are an MFS complaint-resolution communication assistant.

You receive a sanitized transaction snapshot, a deterministic rules-engine decision,
retrieved complaint procedures, and the customer's complaint message.

Rules:
- Never request or reveal a PIN, OTP, password, full phone number, or secret.
- Never claim money was reversed, credited, or recovered unless the transaction data says so.
- Never promise a refund or recovery.
- Never recommend repeating a possibly duplicated transfer.
- Never change the deterministic route, priority, category, or self-resolvable decision.
- Never invent transaction fields.
- Produce a concise operational summary and a respectful customer response.
- Cite only article IDs supplied in the retrieved context.
"""


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client: Any | None = None
        if not self.settings.mock_llm and self.settings.openai_api_key:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "OpenAI mode requires the openai package. Run: pip install -r requirements.txt"
                ) from exc
            self.client = OpenAI(api_key=self.settings.openai_api_key)

    def assess(
        self,
        customer_message: str,
        transaction_context: dict,
        rule_decision: RuleDecision,
        knowledge_hits: list[KnowledgeHit],
    ) -> ComplaintAssessment:
        if self.client is None:
            return self._mock_assessment(customer_message, transaction_context, rule_decision, knowledge_hits)

        payload = {
            "customer_message": customer_message,
            "transaction": transaction_context,
            "rules_decision": rule_decision.model_dump(),
            "knowledge_articles": [hit.model_dump() for hit in knowledge_hits],
        }
        response = self.client.responses.parse(
            model=self.settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            text_format=ComplaintAssessment,
        )
        assessment = response.output_parsed
        if assessment is None:
            raise RuntimeError("OpenAI returned no structured complaint assessment.")
        return self._enforce_rules(assessment, rule_decision, knowledge_hits)

    @staticmethod
    def _enforce_rules(
        assessment: ComplaintAssessment,
        rule_decision: RuleDecision,
        knowledge_hits: list[KnowledgeHit],
    ) -> ComplaintAssessment:
        allowed_articles = {hit.article_id for hit in knowledge_hits}
        return assessment.model_copy(update={
            "category": rule_decision.category,
            "priority": rule_decision.priority,
            "routed_team": rule_decision.routed_team,
            "self_resolvable": rule_decision.self_resolvable,
            "cited_article_ids": [
                article_id for article_id in assessment.cited_article_ids if article_id in allowed_articles
            ],
        })

    @staticmethod
    def _mock_assessment(
        customer_message: str,
        transaction_context: dict,
        rule_decision: RuleDecision,
        knowledge_hits: list[KnowledgeHit],
    ) -> ComplaintAssessment:
        summary = (
            f"Complaint for {transaction_context['reference_number']}: customer reports "
            f"'{customer_message[:180]}'. Status={transaction_context['status']}; "
            f"sender_debited={transaction_context['sender_debited']}; "
            f"receiver_credited={transaction_context['receiver_credited']}; "
            f"reversed={transaction_context['reversed']}. "
            f"Rules classified the case as {rule_decision.category}."
        )
        return ComplaintAssessment(
            category=rule_decision.category,
            priority=rule_decision.priority,
            summary=summary,
            initial_response=rule_decision.safe_initial_response,
            routed_team=rule_decision.routed_team,
            self_resolvable=rule_decision.self_resolvable,
            next_steps=rule_decision.required_actions,
            cited_article_ids=[hit.article_id for hit in knowledge_hits[:3]],
            confidence=0.88,
        )
