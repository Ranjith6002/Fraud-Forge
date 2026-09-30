"""Framework-independent domain objects shared by the rules and the engine.

Nothing in here imports FastAPI, SQLAlchemy or Pydantic, so the fraud rules and the
engine can be unit-tested (and reused) without any infrastructure.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.utils.geo import is_valid_coordinate
from app.utils.timeutils import ensure_utc


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    CLEARED = "CLEARED"


@dataclass(frozen=True)
class TransactionData:
    """The view of a transaction that fraud rules are allowed to see."""

    transaction_id: str
    user_id: str
    amount: float
    currency: str = "INR"
    merchant: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    timestamp: Optional[datetime] = None
    device_id: Optional[str] = None

    @property
    def has_coordinates(self) -> bool:
        return is_valid_coordinate(self.latitude, self.longitude)

    @property
    def utc_timestamp(self) -> Optional[datetime]:
        return ensure_utc(self.timestamp)


@dataclass
class TransactionContext:
    """History available to rules. `history` = the same user's earlier transactions."""

    user_id: str
    history: List[TransactionData] = field(default_factory=list)

    def history_before(self, transaction: TransactionData) -> List[TransactionData]:
        """Earlier transactions (oldest first) with a valid timestamp <= the current one."""
        current_ts = transaction.utc_timestamp
        result = []
        for item in self.history:
            if item.transaction_id == transaction.transaction_id:
                continue
            ts = item.utc_timestamp
            if ts is None:
                continue
            if current_ts is not None and ts > current_ts:
                continue
            result.append(item)
        result.sort(key=lambda t: t.utc_timestamp)
        return result


@dataclass(frozen=True)
class RuleResult:
    rule_name: str
    triggered: bool
    score: int = 0
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskAssessment:
    transaction_id: str
    raw_score: int
    risk_score: int
    risk_level: RiskLevel
    results: List[RuleResult]

    @property
    def flags(self) -> List[RuleResult]:
        return [r for r in self.results if r.triggered]

    @property
    def is_flagged(self) -> bool:
        return any(r.triggered for r in self.results)
