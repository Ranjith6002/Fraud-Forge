from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.engine import FraudEngine, RiskThresholds
from app.rules.factory import load_rules_from_db
from app.rules.registry import build_rules
from app.services.notifications import NotificationService, build_notifier
from app.services.transaction_service import TransactionService

_notifier: Optional[NotificationService] = None


def get_fraud_engine(db: Session = Depends(get_db)) -> FraudEngine:
    s = get_settings()
    thresholds = RiskThresholds(
        medium=s.risk_medium_threshold,
        high=s.risk_high_threshold,
        max_score=s.max_risk_score,
    )
    rules = load_rules_from_db(db)
    if not rules:
        rules = build_rules(s)
    return FraudEngine(rules, thresholds)


def get_notifier() -> NotificationService:
    global _notifier
    if _notifier is None:
        _notifier = build_notifier(get_settings())
    return _notifier


def get_transaction_service(
    db: Session = Depends(get_db),
    engine: FraudEngine = Depends(get_fraud_engine),
    notifier: NotificationService = Depends(get_notifier),
) -> TransactionService:
    s = get_settings()
    return TransactionService(
        db, engine, notifier, notify_threshold=s.notify_threshold, history_days=s.history_days,
        history_limit=s.history_limit, console_url=s.console_url.rstrip("/"),
    )
