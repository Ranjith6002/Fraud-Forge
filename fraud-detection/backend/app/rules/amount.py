from typing import Any, Dict

from app.domain import RuleResult, TransactionContext, TransactionData
from app.rules.base import FraudRule
from app.utils.formatting import format_money


class UnusualAmountRule(FraudRule):
    """Amount far above the user's historical average."""

    name = "UNUSUAL_AMOUNT"
    description = "Transaction amount is much higher than the user's historical average."

    def __init__(self, multiplier: float = 5.0, min_history: int = 3, score: int = 35) -> None:
        super().__init__(score)
        self.multiplier = multiplier
        self.min_history = max(1, int(min_history))

    def parameters(self) -> Dict[str, Any]:
        return {"multiplier": self.multiplier, "min_history": self.min_history}

    def evaluate(self, transaction: TransactionData, context: TransactionContext) -> RuleResult:
        amounts = [
            h.amount
            for h in context.history_before(transaction)
            if isinstance(h.amount, (int, float)) and h.amount > 0
        ]
        if len(amounts) < self.min_history:
            return self.miss(
                f"Not enough history to compare ({len(amounts)} of {self.min_history} "
                "required transactions)."
            )
        average = sum(amounts) / len(amounts)
        ratio = transaction.amount / average
        if transaction.amount > average * self.multiplier:
            cur = transaction.currency
            return self.hit(
                f"Current amount {format_money(transaction.amount, cur)} is {ratio:.1f}x the "
                f"historical average {format_money(average, cur)} (threshold {self.multiplier:g}x).",
                average=round(average, 2),
                ratio=round(ratio, 2),
                history_count=len(amounts),
            )
        return self.miss(f"Amount is {ratio:.1f}x the historical average (threshold {self.multiplier:g}x).")
