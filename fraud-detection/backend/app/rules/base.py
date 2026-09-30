"""The plugin contract every fraud rule implements."""
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.domain import RuleResult, TransactionContext, TransactionData


class FraudRule(ABC):
    """Base class for all fraud rules.

    To add a new rule: subclass this, set `name`/`description`, implement `evaluate`,
    and register the instance (see app/rules/registry.py). The FraudEngine is never edited.
    """

    #: Unique machine name stored on fraud flags, e.g. "HIGH_VELOCITY".
    name: str = ""
    #: One-line human description shown in the console.
    description: str = ""

    def __init__(self, score: int) -> None:
        if not self.name:
            raise ValueError(f"{type(self).__name__} must define a non-empty `name`")
        self.score = int(score)

    @abstractmethod
    def evaluate(self, transaction: TransactionData, context: TransactionContext) -> RuleResult:
        """Inspect the transaction (plus history in `context`) and return a RuleResult."""

    def parameters(self) -> Dict[str, Any]:
        """Configurable thresholds, exposed by GET /api/rules."""
        return {}

    def describe(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "score": self.score,
            "parameters": self.parameters(),
        }

    # --- helpers so concrete rules stay tiny ---------------------------------------------
    def hit(self, reason: str, **details: Any) -> RuleResult:
        return RuleResult(self.name, True, self.score, reason, dict(details))

    def miss(self, reason: str = "Rule did not trigger.", **details: Any) -> RuleResult:
        return RuleResult(self.name, False, 0, reason, dict(details))
