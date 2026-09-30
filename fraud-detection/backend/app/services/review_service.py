import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import ReviewStatus
from app.models import Review, Transaction
from app.services.transaction_service import TransactionNotFoundError
from app.utils.timeutils import utcnow

logger = logging.getLogger(__name__)


class InvalidReviewTransitionError(Exception):
    pass


def apply_review(db: Session, transaction_id: str, reviewer: str, comment: Optional[str],
                 new_status: ReviewStatus) -> Transaction:
    """Change the review status and append an audit row. Fraud flags are never touched."""
    txn = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id).with_for_update())
    if txn is None:
        raise TransactionNotFoundError(f"Transaction '{transaction_id}' not found")
    if txn.review_status == new_status.value:
        raise InvalidReviewTransitionError(f"Transaction is already {new_status.value}")

    now = utcnow()
    db.add(Review(
        transaction_id=txn.transaction_id, reviewer=reviewer.strip(), previous_status=txn.review_status,
        status=new_status.value, comment=(comment or "").strip() or None, reviewed_at=now,
    ))
    txn.review_status = new_status.value
    db.commit()
    db.refresh(txn)
    logger.info("Review recorded", extra={"transaction_id": transaction_id, "status": new_status.value,
                                          "reviewer": reviewer})
    return txn
