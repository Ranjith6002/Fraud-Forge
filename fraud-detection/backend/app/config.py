"""Application settings, loaded from environment variables (and an optional .env file)."""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    app_name: str = "Fraud Rule Engine"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://fraud:fraud@localhost:5432/fraud"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- AWS / notifications (all optional; the app works without them) -------------------
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    sns_topic_arn: Optional[str] = None
    ses_from_email: Optional[str] = None
    alert_email: Optional[str] = None  # one address or a comma-separated list
    #: auto | sns | ses | both | log | none
    notification_provider: str = "auto"
    notify_threshold: int = 70
    console_url: str = "http://localhost:5173"

    # --- Risk scoring ---------------------------------------------------------------------
    risk_medium_threshold: int = 40
    risk_high_threshold: int = 70
    max_risk_score: int = 100

    # --- Rule configuration ---------------------------------------------------------------
    velocity_max_transactions: int = 5
    velocity_window_minutes: float = 10
    velocity_score: int = 30

    amount_multiplier: float = 5.0
    amount_min_history: int = 3
    amount_score: int = 35

    geo_max_speed_kmh: float = 900.0
    geo_min_distance_km: float = 50.0
    geo_score: int = 40

    #: Comma-separated optional rules to enable, e.g. "device_mismatch"
    extra_rules: str = ""

    # --- Context building -----------------------------------------------------------------
    history_days: int = 90
    history_limit: int = 1000

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def extra_rule_list(self) -> List[str]:
        return [r.strip().lower() for r in self.extra_rules.split(",") if r.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
