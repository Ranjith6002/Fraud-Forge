from datetime import timedelta
from typing import Any, Dict

from app.domain import RuleResult, TransactionContext, TransactionData
from app.rules.base import FraudRule


class VelocityRule(FraudRule):
    """Too many transactions by the same user in a short window."""

    name = "HIGH_VELOCITY"
    description = "User made more than N transactions within a short time window."

    def __init__(self, max_transactions: int = 5, window_minutes: float = 10, score: int = 30) -> None:
        super().__init__(score)
        self.max_transactions = max_transactions
        self.window_minutes = window_minutes

    def parameters(self) -> Dict[str, Any]:
        return {"max_transactions": self.max_transactions, "window_minutes": self.window_minutes}

    def evaluate(self, transaction: TransactionData, context: TransactionContext) -> RuleResult:
        ts = transaction.utc_timestamp
        if ts is None:
            return self.miss("Transaction has no valid timestamp.")
        window_start = ts - timedelta(minutes=self.window_minutes)
        earlier = [
            h for h in context.history_before(transaction) if h.utc_timestamp >= window_start
        ]
        count = len(earlier) + 1  # include the current transaction
        if count > self.max_transactions:
            return self.hit(
                f"User made {count} transactions within {self.window_minutes:g} minutes.",
                count=count,
                window_minutes=self.window_minutes,
                threshold=self.max_transactions,
            )
        return self.miss(
            f"{count} transaction(s) in the last {self.window_minutes:g} minutes "
            f"(limit {self.max_transactions}).",
            count=count,
        )
