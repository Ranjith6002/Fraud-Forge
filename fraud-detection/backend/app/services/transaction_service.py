import logging
from datetime import timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain import RiskAssessment, TransactionContext, TransactionData
from app.engine import FraudEngine
from app.models import FraudFlag, Transaction
from app.schemas.transaction import TransactionCreate
from app.services.notifications import HighRiskAlert, NotificationService, dispatch_alert
from app.utils.timeutils import ensure_utc, utcnow

logger = logging.getLogger(__name__)


class DuplicateTransactionError(Exception):
    pass


class TransactionNotFoundError(Exception):
    pass


def to_data(txn: Transaction) -> TransactionData:
    return TransactionData(
        transaction_id=txn.transaction_id, user_id=txn.user_id, amount=float(txn.amount),
        currency=txn.currency, merchant=txn.merchant, latitude=txn.latitude, longitude=txn.longitude,
        location=txn.location, timestamp=ensure_utc(txn.timestamp), device_id=txn.device_id,
    )


class TransactionService:
    """validate -> persist -> build context -> run engine -> persist flags -> notify."""

    def __init__(self, db: Session, engine: FraudEngine, notifier: NotificationService,
                 notify_threshold: int = 70, history_days: int = 90, history_limit: int = 1000,
                 console_url: str = "") -> None:
        self.db = db
        self.engine = engine
        self.notifier = notifier
        self.notify_threshold = notify_threshold
        self.history_days = history_days
        self.history_limit = history_limit
        self.console_url = console_url

    def process(self, payload: TransactionCreate) -> Transaction:
        exists = self.db.scalar(
            select(Transaction.id).where(Transaction.transaction_id == payload.transaction_id)
        )
        if exists is not None:
            raise DuplicateTransactionError(f"Transaction '{payload.transaction_id}' already exists")

        txn = Transaction(
            transaction_id=payload.transaction_id, user_id=payload.user_id, amount=payload.amount,
            currency=payload.currency, merchant=payload.merchant, latitude=payload.latitude,
            longitude=payload.longitude, location=payload.location, device_id=payload.device_id,
            timestamp=ensure_utc(payload.timestamp) or utcnow(),
        )
        self.db.add(txn)
        try:
            self.db.commit()  # persist first: the transaction is never lost, even if scoring fails
        except IntegrityError:
            self.db.rollback()
            raise DuplicateTransactionError(f"Transaction '{payload.transaction_id}' already exists")

        assessment = self.engine.evaluate(to_data(txn), self._build_context(txn))
        self._apply_assessment(txn, assessment)
        self.db.commit()
        logger.info("Transaction evaluated", extra={
            "transaction_id": txn.transaction_id, "risk_score": txn.risk_score, "risk_level": txn.risk_level})
        return txn

    # ------------------------------------------------------------------------------------
    def _build_context(self, txn: Transaction) -> TransactionContext:
        ts = ensure_utc(txn.timestamp)
        rows = self.db.scalars(
            select(Transaction)
            .where(Transaction.user_id == txn.user_id, Transaction.id != txn.id,
                   Transaction.timestamp <= ts,
                   Transaction.timestamp >= ts - timedelta(days=self.history_days))
            .order_by(Transaction.timestamp.desc())
            .limit(self.history_limit)
        ).all()
        history: List[TransactionData] = [to_data(r) for r in reversed(rows)]
        return TransactionContext(user_id=txn.user_id, history=history)

    def _apply_assessment(self, txn: Transaction, assessment: RiskAssessment) -> None:
        txn.risk_score = assessment.risk_score
        txn.risk_level = assessment.risk_level.value
        for result in assessment.flags:
            self.db.add(FraudFlag(
                transaction_id=txn.transaction_id, rule_name=result.rule_name, score=result.score,
                reason=result.reason, risk_level=assessment.risk_level.value,
            ))
        self.db.flush()
        self.db.expire(txn, ["flags"])

        if assessment.risk_score >= self.notify_threshold:
            alert = HighRiskAlert(
                transaction_id=txn.transaction_id, user_id=txn.user_id, amount=float(txn.amount),
                currency=txn.currency, location=txn.location, risk_score=assessment.risk_score,
                risk_level=assessment.risk_level.value, reasons=[f.reason for f in assessment.flags],
                console_url=self.console_url,
            )
            result = dispatch_alert(self.notifier, alert)
            txn.notification_status = result.status
            txn.notification_detail = (result.detail or "")[:500]
        else:
            txn.notification_status = "NOT_REQUIRED"
