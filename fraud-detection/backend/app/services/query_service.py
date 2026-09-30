from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain import ReviewStatus, RiskLevel
from app.models import Transaction

SORT_COLUMNS = {
    "created_at": Transaction.created_at,
    "timestamp": Transaction.timestamp,
    "risk_score": Transaction.risk_score,
    "amount": Transaction.amount,
}


def list_transactions(
    db: Session, *, flagged_only: bool = False, search: Optional[str] = None,
    risk_level: Optional[RiskLevel] = None, status: Optional[ReviewStatus] = None,
    sort_by: str = "timestamp", order: str = "desc", limit: int = 50, offset: int = 0,
) -> Tuple[List[Transaction], int]:
    conditions = []
    if flagged_only:
        conditions.append(Transaction.flags.any())
    if risk_level:
        conditions.append(Transaction.risk_level == risk_level.value)
    if status:
        conditions.append(Transaction.review_status == status.value)
    if search and search.strip():
        raw_search = search.strip()
        needle = raw_search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{needle}%"
        
        # Also build hyphen/space stripped variant for flexible transaction_id and user_id searching
        clean_needle = raw_search.replace("-", "").replace(" ", "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clean_pattern = f"%{clean_needle}%"

        conditions.append(
            Transaction.transaction_id.ilike(pattern, escape="\\")
            | func.replace(func.replace(Transaction.transaction_id, "-", ""), " ", "").ilike(clean_pattern, escape="\\")
            | Transaction.user_id.ilike(pattern, escape="\\")
            | func.replace(func.replace(Transaction.user_id, "-", ""), " ", "").ilike(clean_pattern, escape="\\")
            | Transaction.merchant.ilike(pattern, escape="\\")
            | Transaction.location.ilike(pattern, escape="\\")
        )


    column = SORT_COLUMNS.get(sort_by, Transaction.timestamp)
    primary = column.asc() if order == "asc" else column.desc()

    total = db.scalar(select(func.count()).select_from(Transaction).where(*conditions)) or 0
    items = db.scalars(
        select(Transaction).where(*conditions)
        .options(selectinload(Transaction.flags))
        .order_by(primary, Transaction.timestamp.desc(), Transaction.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return list(items), total


def dashboard_counts(db: Session) -> dict:
    def count(*conds) -> int:
        return db.scalar(select(func.count()).select_from(Transaction).where(*conds)) or 0

    flagged = Transaction.flags.any()
    return {
        "total_transactions": count(),
        "flagged_transactions": count(flagged),
        "high_risk_transactions": count(flagged, Transaction.risk_level == "HIGH"),
        "medium_risk_transactions": count(flagged, Transaction.risk_level == "MEDIUM"),
        "low_risk_flagged_transactions": count(flagged, Transaction.risk_level == "LOW"),
        "pending_reviews": count(flagged, Transaction.review_status == "PENDING"),
        "reviewed_transactions": count(Transaction.review_status == "REVIEWED"),
        "cleared_transactions": count(Transaction.review_status == "CLEARED"),
    }
