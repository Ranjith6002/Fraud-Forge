from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain import ReviewStatus, RiskLevel
from app.utils.timeutils import ensure_utc, utcnow


class TransactionCreate(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.:\-]+$",
                                examples=["TX1001"])
    user_id: str = Field(min_length=1, max_length=64, examples=["U999"])
    amount: float = Field(gt=0, lt=1_000_000_000_000, examples=[95000])
    currency: str = Field(default="INR", min_length=3, max_length=3)
    merchant: Optional[str] = Field(default=None, max_length=128)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    location: str = Field(min_length=1, max_length=128, examples=["London"])
    device_id: Optional[str] = Field(default=None, max_length=128)
    timestamp: Optional[datetime] = Field(default=None, description="Defaults to now (UTC).")

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("location")
    @classmethod
    def _valid_location(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Location is required.")
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def _valid_timestamp(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return None
        v = ensure_utc(v)
        if v > utcnow() + timedelta(minutes=10):
            raise ValueError("timestamp cannot be in the future")
        return v

    @model_validator(mode="after")
    def _coords_together(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class FlagOut(BaseModel):
    rule: str
    score: int
    reason: str


class RuleResultOut(BaseModel):
    rule: str
    description: str
    triggered: bool
    score: int
    reason: str


class ReviewOut(BaseModel):
    id: int
    reviewer: str
    previous_status: str
    status: str
    comment: Optional[str] = None
    reviewed_at: datetime


class EvaluationOut(BaseModel):
    """Response of POST /api/transactions."""

    transaction_id: str
    risk_score: int
    risk_level: RiskLevel
    flags: List[FlagOut]
    review_status: ReviewStatus
    notification_status: str
    notification_detail: Optional[str] = None


class TransactionSummary(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant: Optional[str] = None
    location: Optional[str] = None
    timestamp: datetime
    risk_score: int
    risk_level: RiskLevel
    review_status: ReviewStatus
    triggered_rules: List[str]
    created_at: datetime


class TransactionDetail(TransactionSummary):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_id: Optional[str] = None
    notification_status: str
    notification_detail: Optional[str] = None
    flags: List[FlagOut]
    rule_results: List[RuleResultOut]
    reviews: List[ReviewOut]


class TransactionList(BaseModel):
    items: List[TransactionSummary]
    total: int


class ReviewAction(BaseModel):
    reviewer: str = Field(min_length=1, max_length=64, examples=["admin"])
    comment: Optional[str] = Field(default=None, max_length=2000, examples=["Verified with customer."])


class DashboardStats(BaseModel):
    total_transactions: int
    flagged_transactions: int
    high_risk_transactions: int
    medium_risk_transactions: int
    low_risk_flagged_transactions: int
    pending_reviews: int
    reviewed_transactions: int
    cleared_transactions: int
    recent_suspicious: List[TransactionSummary]


class RuleInfo(BaseModel):
    name: str
    description: str
    score: int
    parameters: dict


class SeedResult(BaseModel):
    created: int
    flagged: int
    high_risk: int
    medium_risk: int
    demo_transaction_id: str
    message: str
