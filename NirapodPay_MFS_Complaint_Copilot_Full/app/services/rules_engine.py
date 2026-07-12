from datetime import datetime, timezone
from app.models import Transaction
from app.schemas import RuleDecision


def _age_minutes(transaction: Transaction) -> float:
    initiated = transaction.initiated_at
    if initiated.tzinfo is None:
        initiated = initiated.replace(tzinfo=timezone.utc)
    return max((datetime.now(timezone.utc) - initiated).total_seconds() / 60, 0)


def evaluate_transaction(transaction: Transaction, customer_message: str) -> RuleDecision:
    message = customer_message.lower()
    cross_mfs = transaction.source_mfs != transaction.target_mfs
    age_minutes = _age_minutes(transaction)

    if any(term in message for term in ("unauthorized", "not me", "did not send", "didn't send", "fraud", "hacked")):
        return RuleDecision(
            category="unauthorized_transfer", priority="urgent", routed_team="Fraud and Risk",
            self_resolvable=False,
            safe_initial_response=(
                "I have marked this complaint as urgent. Do not share a PIN, password, or OTP. "
                "A fraud specialist must review the transaction through an authenticated channel."
            ),
            required_actions=[
                "Apply approved account-protection controls.",
                "Review authentication, device, and session events.",
                "Contact the customer through an authenticated channel.",
            ],
            reason_codes=["CUSTOMER_DENIES_TRANSACTION", "FRAUD_REVIEW_REQUIRED"],
        )

    if "wrong number" in message or "wrong receiver" in message:
        return RuleDecision(
            category="wrong_receiver", priority="high", routed_team="Disputes and Chargeback",
            self_resolvable=False,
            safe_initial_response=(
                "A completed transfer to the wrong receiver cannot be automatically reversed by the chatbot. "
                "A controlled dispute case has been created."
            ),
            required_actions=[
                "Verify transaction authorization.",
                "Start the wrong-beneficiary dispute procedure.",
                "Do not promise recovery before investigation.",
            ],
            reason_codes=["WRONG_BENEFICIARY_CLAIM"],
        )

    if transaction.reversed or transaction.status == "REVERSED":
        return RuleDecision(
            category="reversed_transfer", priority="low", routed_team="Customer Support",
            self_resolvable=True,
            safe_initial_response=(
                "The transaction is recorded as reversed. The returned amount should appear in the sender wallet "
                "statement. Refresh the wallet and check the latest balance and statement."
            ),
            required_actions=["Show the confirmed reversal status.", "Advise the customer to inspect the sender statement."],
            reason_codes=["REVERSAL_CONFIRMED"],
        )

    if transaction.status == "FAILED" and transaction.sender_debited and not transaction.reversed:
        return RuleDecision(
            category="failed_debited", priority="high", routed_team="Auto-Reversal Operations",
            self_resolvable=False,
            safe_initial_response=(
                "The transfer failed, but the sender debit is still recorded. A reversal investigation is required "
                "and has been routed to the responsible team."
            ),
            required_actions=[
                "Check the reversal ledger and switch response code.",
                "Start the approved reversal workflow when eligible.",
                "Reconcile the sender ledger after completion.",
            ],
            reason_codes=["FAILED_AFTER_DEBIT", transaction.failure_code or "NO_FAILURE_CODE"],
        )

    if transaction.status == "PENDING":
        if age_minutes <= 15:
            return RuleDecision(
                category="pending_transfer", priority="low", routed_team="Customer Support",
                self_resolvable=True,
                safe_initial_response=(
                    "The transaction is still inside the normal processing window. Wait a few minutes and check again. "
                    "Do not repeat the transfer while it is pending."
                ),
                required_actions=["Do not submit a duplicate transfer.", "Recheck after the normal processing window."],
                reason_codes=["PENDING_WITHIN_NORMAL_WINDOW"],
            )
        return RuleDecision(
            category="pending_transfer", priority="high" if cross_mfs else "medium",
            routed_team="Interoperability and Settlement" if cross_mfs else "Switch Operations",
            self_resolvable=False,
            safe_initial_response=(
                "The transaction has remained pending beyond the normal processing window. It has been routed for "
                "switch and settlement investigation."
            ),
            required_actions=[
                "Trace the switch-message lifecycle.",
                "Check settlement and acknowledgement records.",
                "Prevent duplicate manual posting.",
            ],
            reason_codes=["PENDING_BEYOND_SLA", "CROSS_MFS" if cross_mfs else "SAME_MFS"],
        )

    receiver_terms = ("receiver did not", "receiver didn't", "not received", "not credited", "recipient")
    if transaction.status == "COMPLETED" and any(term in message for term in receiver_terms):
        return RuleDecision(
            category="receiver_not_credited", priority="high" if cross_mfs else "medium",
            routed_team="Interoperability and Settlement" if cross_mfs else "Recipient Wallet Operations",
            self_resolvable=False,
            safe_initial_response=(
                "The switch records the transfer as completed, but the receiver reports no credit. The receiving "
                "ledger and settlement acknowledgement must be checked."
            ),
            required_actions=[
                "Verify the receiver-ledger posting.",
                "Compare switch completion with the wallet-credit event.",
                "Check cross-MFS settlement acknowledgement when applicable.",
            ],
            reason_codes=["COMPLETED_RECEIVER_NOT_CREDITED", "CROSS_MFS" if cross_mfs else "SAME_MFS"],
        )

    if "fee" in message or "charged" in message or "amount" in message:
        return RuleDecision(
            category="fee_or_amount_dispute", priority="medium", routed_team="Finance Reconciliation",
            self_resolvable=False,
            safe_initial_response=(
                "The amount or fee must be reconciled against the approved tariff and transaction ledger. "
                "A finance-review case has been created."
            ),
            required_actions=["Compare the applied fee with the active tariff.", "Verify debit, credit, and fee entries."],
            reason_codes=["FEE_OR_AMOUNT_DISPUTE"],
        )

    if transaction.status == "COMPLETED":
        return RuleDecision(
            category="unknown", priority="low", routed_team="Customer Support", self_resolvable=True,
            safe_initial_response=(
                "The transaction is recorded as completed. Review the displayed details and explain what remains "
                "incorrect so the complaint can be classified more precisely."
            ),
            required_actions=["Ask for the unresolved symptom without requesting a PIN or OTP."],
            reason_codes=["COMPLETED_NO_SPECIFIC_FAILURE"],
        )

    return RuleDecision(
        category="unknown", priority="medium", routed_team="Customer Support", self_resolvable=False,
        safe_initial_response=(
            "The available transaction fields do not match a safe automatic resolution. A support case has been "
            "created for manual review."
        ),
        required_actions=["Review the transaction and complaint details manually."],
        reason_codes=["NO_RULE_MATCH"],
    )
