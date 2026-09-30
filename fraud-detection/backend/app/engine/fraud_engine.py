"""The fraud engine.

It knows NOTHING about individual rules: it receives a list of `FraudRule` objects
(dependency inversion), runs each one, sums the scores, caps them and maps to a level.
"""
import logging
from typing import Iterable, List, Optional, Tuple

from app.domain import RiskAssessment, RuleResult, TransactionContext, TransactionData
from app.engine.scoring import RiskThresholds
from app.rules.base import FraudRule

logger = logging.getLogger(__name__)


class FraudEngine:
    def __init__(self, rules: Iterable[FraudRule], thresholds: Optional[RiskThresholds] = None) -> None:
        self._rules: List[FraudRule] = []
        self.thresholds = thresholds or RiskThresholds()
        for rule in rules:
            self.register(rule)

    @property
    def rules(self) -> Tuple[FraudRule, ...]:
        return tuple(self._rules)

    def register(self, rule: FraudRule) -> None:
        if any(r.name == rule.name for r in self._rules):
            raise ValueError(f"A rule named '{rule.name}' is already registered")
        self._rules.append(rule)

    def evaluate(self, transaction: TransactionData, context: TransactionContext) -> RiskAssessment:
        results: List[RuleResult] = []
        for rule in self._rules:
            try:
                result = rule.evaluate(transaction, context)
            except Exception as exc:  # one broken rule must never break scoring
                logger.exception("Fraud rule failed", extra={"rule": rule.name})
                result = RuleResult(rule.name, False, 0, f"Rule error: {exc}", {"error": True})
            if not result.triggered and result.score:
                result = RuleResult(result.rule_name, False, 0, result.reason, result.details)
            results.append(result)

        raw = sum(max(0, r.score) for r in results if r.triggered)
        score = self.thresholds.clamp(raw)
        return RiskAssessment(
            transaction_id=transaction.transaction_id,
            raw_score=raw,
            risk_score=score,
            risk_level=self.thresholds.level_for(score),
            results=results,
        )
