from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_fraud_engine, get_transaction_service
from app.api.serializers import to_summary
from app.database import get_db
from app.engine import FraudEngine
from app.schemas.transaction import DashboardStats, RuleInfo, SeedResult
from app.services import query_service
from app.services.seed_service import seed_demo_data
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats, summary="Dashboard statistics")
def dashboard_stats(db: Session = Depends(get_db)):
    counts = query_service.dashboard_counts(db)
    recent, _ = query_service.list_transactions(
        db, flagged_only=True, sort_by="timestamp", order="desc", limit=8)
    return DashboardStats(**counts, recent_suspicious=[to_summary(t) for t in recent])


@router.get("/rules", response_model=List[RuleInfo], summary="Registered fraud rules")
def list_rules(engine: FraudEngine = Depends(get_fraud_engine)):
    return [RuleInfo(**rule.describe()) for rule in engine.rules]


@router.post("/seed", response_model=SeedResult, summary="Generate demo data (resets existing data by default)")
def seed(reset: bool = True, db: Session = Depends(get_db),
         service: TransactionService = Depends(get_transaction_service)):
    return seed_demo_data(db, service, reset=reset)
