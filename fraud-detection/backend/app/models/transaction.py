from datetime import datetime
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, Float, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.timeutils import utcnow


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_ts", "user_id", "timestamp"),
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    merchant: Mapped[Optional[str]] = mapped_column(String(128))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String(128), nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    # Result of the fraud evaluation (denormalised for fast filtering/sorting).
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, default="LOW", index=True)
    review_status: Mapped[str] = mapped_column(String(10), nullable=False, default="PENDING", index=True)
    notification_status: Mapped[str] = mapped_column(String(16), nullable=False, default="NOT_REQUIRED")
    notification_detail: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    flags: Mapped[List["FraudFlag"]] = relationship(
        "FraudFlag", back_populates="transaction", cascade="all, delete-orphan", order_by="FraudFlag.id"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="transaction", cascade="all, delete-orphan", order_by="Review.id"
    )

    @property
    def triggered_rules(self) -> List[str]:
        return [f.rule_name for f in self.flags]
