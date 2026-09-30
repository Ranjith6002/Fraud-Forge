import logging

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import FraudFlag, Review, Transaction
from app.schemas.transaction import SeedResult, TransactionCreate
from app.services.seed_data import DEMO_FRAUD_ID, build_demo_dataset
from app.services.transaction_service import TransactionService
from app.utils.timeutils import utcnow

logger = logging.getLogger(__name__)


def seed_demo_data(db: Session, service: TransactionService, reset: bool = True) -> SeedResult:
    if reset:
        db.execute(delete(Review))
        db.execute(delete(FraudFlag))
        db.execute(delete(Transaction))
        db.commit()

    created = flagged = high = medium = 0
    for row in build_demo_dataset(utcnow()):
        txn = service.process(TransactionCreate(**row))  # same path as real traffic
        created += 1
        if txn.flags:
            flagged += 1
        if txn.risk_level == "HIGH" and txn.flags:
            high += 1
        elif txn.risk_level == "MEDIUM" and txn.flags:
            medium += 1
    logger.info("Demo data seeded", extra={"created": created, "flagged": flagged})
    return SeedResult(
        created=created, flagged=flagged, high_risk=high, medium_risk=medium,
        demo_transaction_id=DEMO_FRAUD_ID,
        message=f"Seeded {created} transactions ({flagged} flagged). Open {DEMO_FRAUD_ID} for the full-fraud demo.",
    )
