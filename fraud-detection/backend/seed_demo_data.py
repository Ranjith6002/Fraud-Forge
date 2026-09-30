#!/usr/bin/env python3
"""
CLI seed script to populate the Supabase PostgreSQL database with realistic demo data.

Usage:
    python seed_demo_data.py               # Seed database with realistic demo dataset
    python seed_demo_data.py --dry-run     # Preview dataset evaluation without modifying DB
    python seed_demo_data.py --reset       # Reset existing transactions before seeding
    python seed_demo_data.py --no-reset    # Append new demo data without clearing existing DB
"""
import sys
import os
import argparse
import logging

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import get_settings
from app.database import engine, SessionLocal
from app.rules.registry import build_rules

from app.engine.fraud_engine import FraudEngine
from app.engine.scoring import RiskThresholds
from app.services.notifications import LoggingNotificationService

from app.services.transaction_service import TransactionService
from app.services.seed_service import seed_demo_data, seed_rules_if_needed
from app.services.seed_data import build_demo_dataset, DEMO_FRAUD_ID
from app.schemas.transaction import TransactionCreate
from app.utils.timeutils import utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_demo_data")


def run_dry_run():
    """Evaluate demo dataset in-memory without altering Supabase database."""
    print("=" * 65)
    print("               DRY RUN PREVIEW (NO DB MUTATIONS)             ")
    print("=" * 65)
    settings = get_settings()
    rules = build_rules(settings)
    engine_inst = FraudEngine(rules=rules, thresholds=RiskThresholds(medium=30, high=70))


    now = utcnow()
    dataset = build_demo_dataset(now)

    total = len(dataset)
    low_count = 0
    med_count = 0
    high_count = 0
    flagged_count = 0
    velocity_count = 0
    amount_count = 0
    geo_count = 0
    multi_count = 0

    from app.domain import TransactionContext, TransactionData
    user_history = {}

    for row in dataset:
        tx_id = row["transaction_id"]
        user_id = row["user_id"]
        t_data = TransactionData(
            transaction_id=tx_id,
            user_id=user_id,
            amount=row["amount"],
            currency=row["currency"],
            merchant=row.get("merchant"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            location=row["location"],
            timestamp=row["timestamp"],
            device_id=row.get("device_id"),
        )
        history = user_history.get(user_id, [])
        ctx = TransactionContext(user_id=user_id, history=history)
        assessment = engine_inst.evaluate(t_data, ctx)
        user_history.setdefault(user_id, []).append(t_data)

        if assessment.risk_level.value == "HIGH":
            high_count += 1
        elif assessment.risk_level.value == "MEDIUM":
            med_count += 1
        else:
            low_count += 1

        triggered_rule_names = [f.rule_name for f in assessment.flags]
        if triggered_rule_names:
            flagged_count += 1
            if len(triggered_rule_names) > 1:
                multi_count += 1
            if "HIGH_VELOCITY" in triggered_rule_names:
                velocity_count += 1
            if "UNUSUAL_AMOUNT" in triggered_rule_names:
                amount_count += 1
            if "IMPOSSIBLE_GEO" in triggered_rule_names:
                geo_count += 1

    print(f"Total Transactions Evaluated : {total}")
    print(f"LOW Risk Transactions         : {low_count}")
    print(f"MEDIUM Risk Transactions      : {med_count}")
    print(f"HIGH Risk Transactions        : {high_count}")
    print(f"Flagged Transactions          : {flagged_count}")
    print(f"  |-- Velocity Scenarios      : {velocity_count}")
    print(f"  |-- Unusual Amount Scenarios: {amount_count}")
    print(f"  |-- Impossible Geo Scenarios: {geo_count}")
    print(f"  +-- Multi-Rule Scenarios    : {multi_count}")
    print("=" * 65)
    print("Dry run complete. No changes were made to Supabase.")



def main():
    parser = argparse.ArgumentParser(description="Seed FraudForge database with realistic demo data.")
    parser.add_argument("--dry-run", action="store_true", help="Preview seed evaluation without saving to database.")
    parser.add_argument("--reset", action="store_true", default=True, help="Reset existing transaction data before seeding (default).")
    parser.add_argument("--no-reset", action="store_false", dest="reset", help="Keep existing transaction data and append demo records.")
    args = parser.parse_args()

    if args.dry_run:
        run_dry_run()
        return

    settings = get_settings()
    logger.info("Connecting to Supabase PostgreSQL database...")
    logger.info(f"App: {settings.app_name}")

    rules = build_rules(settings)
    engine_inst = FraudEngine(rules=rules, thresholds=RiskThresholds(medium=settings.risk_medium_threshold, high=settings.risk_high_threshold))

    notifier = LoggingNotificationService()

    db = SessionLocal()
    try:
        service = TransactionService(
            db=db,
            engine=engine_inst,
            notifier=notifier,
            notify_threshold=settings.notify_threshold,
            history_days=settings.history_days,
            history_limit=settings.history_limit,
        )

        print("Starting Supabase database seeding...")
        result = seed_demo_data(db, service, reset=args.reset)
        print("=" * 65)
        print("                  SEEDING COMPLETED SUCCESSFULLY             ")
        print("=" * 65)
        print(f"Message            : {result.message}")
        print(f"Transactions Seeded: {result.created}")
        print(f"Flagged Count      : {result.flagged}")
        print(f"HIGH Risk Count    : {result.high_risk}")
        print(f"MEDIUM Risk Count  : {result.medium_risk}")
        print(f"Demo Transaction ID: {result.demo_transaction_id}")
        print("=" * 65)
    finally:
        db.close()



if __name__ == "__main__":
    main()
