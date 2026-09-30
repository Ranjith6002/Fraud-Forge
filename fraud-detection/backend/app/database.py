import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool  # one shared in-memory DB (used by tests)
    else:
        kwargs["pool_pre_ping"] = True
    return create_engine(url, **kwargs)


engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    """Create tables, waiting for the database to accept connections (docker start-up)."""
    from app import models  # noqa: F401  (registers the tables on Base.metadata)
    from app.models.rule import RuleModel
    from app.config import get_settings

    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)

            # Seed default rules into DB if none exist
            db = SessionLocal()
            try:
                # Fix null locations if any exist from legacy records
                try:
                    db.execute(text("UPDATE transactions SET location = 'Unknown' WHERE location IS NULL"))
                    db.commit()
                except Exception:
                    db.rollback()

                count = db.scalar(text("SELECT count(*) FROM rules"))
                if not count:
                    s = get_settings()
                    defaults = [
                        RuleModel(
                            name="HIGH_VELOCITY",
                            rule_type="VELOCITY",
                            description="User made more than N transactions within a short time window.",
                            enabled=True,
                            risk_score=s.velocity_score,
                            parameters={
                                "max_transactions": s.velocity_max_transactions,
                                "window_minutes": s.velocity_window_minutes,
                            },
                        ),
                        RuleModel(
                            name="UNUSUAL_AMOUNT",
                            rule_type="AMOUNT",
                            description="Transaction amount is much higher than the user's historical average.",
                            enabled=True,
                            risk_score=s.amount_score,
                            parameters={
                                "multiplier": s.amount_multiplier,
                                "min_history": s.amount_min_history,
                            },
                        ),
                        RuleModel(
                            name="IMPOSSIBLE_GEO",
                            rule_type="GEO",
                            description="Travel speed between consecutive transactions exceeds a physical limit.",
                            enabled=True,
                            risk_score=s.geo_score,
                            parameters={
                                "max_speed_kmh": s.geo_max_speed_kmh,
                                "min_distance_km": s.geo_min_distance_km,
                            },
                        ),
                    ]
                    db.add_all(defaults)
                    db.commit()
            finally:
                db.close()

            logger.info("Database ready with default rules seeded")
            return
        except Exception as exc:
            logger.warning("Database not ready (attempt %s/%s): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database")
