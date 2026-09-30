"""ORM -> response schema conversion (explicit, so the API contract is easy to read)."""
from app.engine import FraudEngine
from app.models import Transaction
from app.schemas.transaction import (
    EvaluationOut, FlagOut, ReviewOut, RuleResultOut, TransactionDetail, TransactionSummary,
)


def _flags(txn: Transaction):
    return [FlagOut(rule=f.rule_name, score=f.score, reason=f.reason) for f in txn.flags]


def to_summary(txn: Transaction) -> TransactionSummary:
    return TransactionSummary(
        transaction_id=txn.transaction_id, user_id=txn.user_id, amount=float(txn.amount),
        currency=txn.currency, merchant=txn.merchant, location=txn.location, timestamp=txn.timestamp,
        risk_score=txn.risk_score, risk_level=txn.risk_level, review_status=txn.review_status,
        triggered_rules=txn.triggered_rules, created_at=txn.created_at,
    )


def to_evaluation(txn: Transaction) -> EvaluationOut:
    return EvaluationOut(
        transaction_id=txn.transaction_id, risk_score=txn.risk_score, risk_level=txn.risk_level,
        flags=_flags(txn), review_status=txn.review_status,
        notification_status=txn.notification_status, notification_detail=txn.notification_detail,
    )


def to_detail(txn: Transaction, engine: FraudEngine) -> TransactionDetail:
    """Includes one entry per *registered* rule (triggered or not) so reviewers see the full picture."""
    by_rule = {f.rule_name: f for f in txn.flags}
    results = []
    for rule in engine.rules:
        flag = by_rule.pop(rule.name, None)
        if flag:
            results.append(RuleResultOut(rule=rule.name, description=rule.description, triggered=True,
                                         score=flag.score, reason=flag.reason))
        else:
            results.append(RuleResultOut(rule=rule.name, description=rule.description, triggered=False,
                                         score=0, reason="Rule did not trigger for this transaction."))
    for flag in by_rule.values():  # flags from rules that are no longer registered stay visible
        results.append(RuleResultOut(rule=flag.rule_name, description="(rule no longer registered)",
                                     triggered=True, score=flag.score, reason=flag.reason))
    summary = to_summary(txn).model_dump()
    return TransactionDetail(
        **summary, latitude=txn.latitude, longitude=txn.longitude, device_id=txn.device_id,
        notification_status=txn.notification_status, notification_detail=txn.notification_detail,
        flags=_flags(txn), rule_results=results,
        reviews=[ReviewOut(id=r.id, reviewer=r.reviewer, previous_status=r.previous_status, status=r.status,
                           comment=r.comment, reviewed_at=r.reviewed_at) for r in txn.reviews],
    )
