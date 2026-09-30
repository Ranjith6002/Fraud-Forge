"""Example of an *extra* rule, added WITHOUT touching FraudEngine.

It is disabled by default. Enable it with `EXTRA_RULES=device_mismatch` (see README).
"""
from typing import Any, Dict

from app.domain import RuleResult, TransactionContext, TransactionData
from app.rules.base import FraudRule


class DeviceMismatchRule(FraudRule):
    name = "DEVICE_MISMATCH"
    description = "Transaction made from a device the user has never used before."

    def __init__(self, min_history: int = 1, score: int = 25) -> None:
        super().__init__(score)
        self.min_history = min_history

    def parameters(self) -> Dict[str, Any]:
        return {"min_history": self.min_history}

    def evaluate(self, transaction: TransactionData, context: TransactionContext) -> RuleResult:
        if not transaction.device_id:
            return self.miss("Transaction has no device id.")
        known = {h.device_id for h in context.history_before(transaction) if h.device_id}
        if len(known) < self.min_history:
            return self.miss("No device history for this user yet.")
        if transaction.device_id not in known:
            return self.hit(
                f"Device '{transaction.device_id}' has not been used by this user before "
                f"({len(known)} known device(s)).",
                known_devices=len(known),
            )
        return self.miss("Device is known for this user.")
