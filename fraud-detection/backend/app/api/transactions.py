from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_fraud_engine, get_transaction_service
from app.api.serializers import to_detail, to_evaluation, to_summary
from app.database import get_db
from app.domain import ReviewStatus, RiskLevel
from app.engine import FraudEngine
from app.models import Transaction
from app.schemas.transaction import (
    EvaluationOut, ReviewAction, TransactionCreate, TransactionDetail, TransactionList,
)
from app.services import query_service
from app.services.review_service import InvalidReviewTransitionError, apply_review
from app.services.transaction_service import (
    DuplicateTransactionError, TransactionNotFoundError, TransactionService,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

SortBy = Literal["created_at", "timestamp", "risk_score", "amount"]
Order = Literal["asc", "desc"]


@router.post("", response_model=EvaluationOut, status_code=201, summary="Create and evaluate a transaction")
def create_transaction(payload: TransactionCreate, service: TransactionService = Depends(get_transaction_service)):
    try:
        txn = service.process(payload)
    except DuplicateTransactionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return to_evaluation(txn)


@router.get("", response_model=TransactionList, summary="List transactions")
def list_all(
    q: Optional[str] = Query(None, max_length=100, description="Search id, user, merchant, location"),
    risk_level: Optional[RiskLevel] = None,
    status: Optional[ReviewStatus] = None,
    sort_by: SortBy = "timestamp",
    order: Order = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = query_service.list_transactions(
        db, search=q, risk_level=risk_level, status=status, sort_by=sort_by, order=order,
        limit=limit, offset=offset)
    return TransactionList(items=[to_summary(t) for t in items], total=total)


@router.get("/flagged", response_model=TransactionList, summary="List flagged transactions")
def list_flagged(
    q: Optional[str] = Query(None, max_length=100),
    risk_level: Optional[RiskLevel] = None,
    status: Optional[ReviewStatus] = None,
    sort_by: SortBy = "risk_score",
    order: Order = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = query_service.list_transactions(
        db, flagged_only=True, search=q, risk_level=risk_level, status=status, sort_by=sort_by,
        order=order, limit=limit, offset=offset)
    return TransactionList(items=[to_summary(t) for t in items], total=total)


@router.get("/{transaction_id}", response_model=TransactionDetail, summary="Transaction with fraud evaluation")
def get_transaction(transaction_id: str, db: Session = Depends(get_db),
                    engine: FraudEngine = Depends(get_fraud_engine)):
    txn = db.scalar(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
        .options(selectinload(Transaction.flags), selectinload(Transaction.reviews))
    )
    if txn is None:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    return to_detail(txn, engine)


def _review(transaction_id: str, body: ReviewAction, status: ReviewStatus, db: Session, engine: FraudEngine):
    try:
        apply_review(db, transaction_id, body.reviewer, body.comment, status)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except InvalidReviewTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    txn = db.scalar(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
        .options(selectinload(Transaction.flags), selectinload(Transaction.reviews))
    )
    return to_detail(txn, engine)


@router.patch("/{transaction_id}/review", response_model=TransactionDetail, summary="Mark as REVIEWED")
def mark_reviewed(transaction_id: str, body: ReviewAction, db: Session = Depends(get_db),
                  engine: FraudEngine = Depends(get_fraud_engine)):
    return _review(transaction_id, body, ReviewStatus.REVIEWED, db, engine)


@router.patch("/{transaction_id}/clear", response_model=TransactionDetail, summary="Mark as CLEARED")
def clear_transaction(transaction_id: str, body: ReviewAction, db: Session = Depends(get_db),
                      engine: FraudEngine = Depends(get_fraud_engine)):
    return _review(transaction_id, body, ReviewStatus.CLEARED, db, engine)
