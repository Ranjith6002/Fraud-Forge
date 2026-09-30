import logging
from typing import Dict, Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain import ReviewStatus
from app.models import FraudFlag, Review, RuleModel, Transaction
from app.schemas.transaction import SeedResult, TransactionCreate
from app.services.notifications import LoggingNotificationService

from app.services.review_service import apply_review
from app.services.seed_data import DEMO_FRAUD_ID, build_demo_dataset
from app.services.transaction_service import TransactionService
from app.utils.timeutils import utcnow

logger = logging.getLogger(__name__)

DEFAULT_RULES = [
    {
        "name": "HIGH_VELOCITY",
        "rule_type": "VELOCITY",
        "description": "User made more than 5 transactions within 10 minutes.",
        "enabled": True,
        "risk_score": 30,
        "parameters": {"max_transactions": 5, "window_minutes": 10.0},
    },
    {
        "name": "UNUSUAL_AMOUNT",
        "rule_type": "AMOUNT",
        "description": "Transaction amount is 5x higher than the user's historical average.",
        "enabled": True,
        "risk_score": 35,
        "parameters": {"multiplier": 5.0, "min_history": 3},
    },
    {
        "name": "IMPOSSIBLE_GEO",
        "rule_type": "GEO",
        "description": "Travel speed between consecutive transactions exceeds 900 km/h.",
        "enabled": True,
        "risk_score": 40,
        "parameters": {"max_speed_kmh": 900.0, "min_distance_km": 50.0},
    },
    {
        "name": "DEVICE_MISMATCH",
        "rule_type": "DEVICE_MISMATCH",
        "description": "Transaction made from a device the user has never used before.",
        "enabled": False,
        "risk_score": 25,
        "parameters": {"min_history": 1},
    },
]


def seed_rules_if_needed(db: Session, reset: bool = False) -> None:
    """Ensure standard dynamic rules exist in the rules table."""
    if reset:
        db.execute(delete(RuleModel))
        db.commit()

    for r_def in DEFAULT_RULES:
        existing = db.scalar(select(RuleModel).where(RuleModel.name == r_def["name"]))
        if existing is None:
            rule = RuleModel(
                name=r_def["name"],
                rule_type=r_def["rule_type"],
                description=r_def["description"],
                enabled=r_def["enabled"],
                risk_score=r_def["risk_score"],
                parameters=r_def["parameters"],
            )
            db.add(rule)
    db.commit()


def seed_demo_data(db: Session, service: TransactionService, reset: bool = True) -> SeedResult:
    service.notifier = LoggingNotificationService()


    try:
        # 1. Seed dynamic rule configurations
        seed_rules_if_needed(db, reset=reset)

        # 2. Reset transaction tables if requested
        if reset:
            db.execute(delete(Review))
            db.execute(delete(FraudFlag))
            db.execute(delete(Transaction))
            db.commit()

        created = flagged = high = medium = 0
        dataset = build_demo_dataset(utcnow())

        for row in dataset:
            tx_id = row.get("transaction_id")
            # If reset is False, skip already existing transaction IDs for idempotency
            if not reset and tx_id:
                exists = db.scalar(select(Transaction.id).where(Transaction.transaction_id == tx_id))
                if exists:
                    continue

            txn = service.process(TransactionCreate(**row))  # standard engine evaluation path
            created += 1
            if txn.flags:
                flagged += 1
            if txn.risk_level == "HIGH" and txn.flags:
                high += 1
            elif txn.risk_level == "MEDIUM" and txn.flags:
                medium += 1

        # 3. Seed realistic reviewer actions for sample suspicious transactions
        sample_reviews = [
            ("TX-AMT-HIGH-01", "Analyst Vikram", "High amount flagged. Customer identity & purchase verified via OTP.", ReviewStatus.REVIEWED),
            ("TX-GEO-HIGH-01", "Lead Security Analyst Priya", "Customer confirmed active flight roaming and valid card use in NY.", ReviewStatus.CLEARED),
            ("TX-GEO-HIGH-02", "Analyst Rajesh", "Impossible travel flagged. Card locked pending customer confirmation.", ReviewStatus.REVIEWED),
            ("TX-MULTI-HIGH-01", "Senior Fraud Ops", "High risk multi-rule anomaly. Escalated to tier-2 security audit.", ReviewStatus.REVIEWED),
        ]
        for tx_id, reviewer, comment, status in sample_reviews:
            try:
                apply_review(db, tx_id, reviewer, comment, status)
            except Exception as e:
                logger.debug(f"Review seed skipped for {tx_id}: {e}")

        logger.info("Demo data seeded: %d created, %d flagged", created, flagged)
        return SeedResult(
            created=created,
            flagged=flagged,
            high_risk=high,
            medium_risk=medium,
            demo_transaction_id=DEMO_FRAUD_ID,
            message=f"Seeded {created} transactions ({flagged} flagged, {high} high risk). Open {DEMO_FRAUD_ID} for the full-fraud demo.",
        )
    finally:
        pass


