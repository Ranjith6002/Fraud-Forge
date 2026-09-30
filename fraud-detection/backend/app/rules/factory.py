from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rule import RuleModel
from app.rules.amount import UnusualAmountRule
from app.rules.base import FraudRule
from app.rules.device_mismatch import DeviceMismatchRule
from app.rules.geo import ImpossibleGeoRule
from app.rules.velocity import VelocityRule


def build_rule_from_model(model: RuleModel) -> FraudRule:
    rule_type = model.rule_type.upper()
    params = model.parameters or {}
    score = model.risk_score

    rule: FraudRule
    if rule_type == "VELOCITY":
        max_tx = int(params.get("max_transactions", params.get("threshold", 5)))
        win_min = float(params.get("window_minutes", 10.0))
        rule = VelocityRule(max_transactions=max_tx, window_minutes=win_min, score=score)
    elif rule_type in ("AMOUNT", "UNUSUAL_AMOUNT"):
        mult = float(params.get("multiplier", 5.0))
        min_hist = int(params.get("min_history", 3))
        rule = UnusualAmountRule(multiplier=mult, min_history=min_hist, score=score)
    elif rule_type in ("GEO", "IMPOSSIBLE_GEO"):
        max_speed = float(params.get("max_speed_kmh", params.get("maximum_speed_kmh", 900.0)))
        min_dist = float(params.get("min_distance_km", 50.0))
        rule = ImpossibleGeoRule(max_speed_kmh=max_speed, min_distance_km=min_dist, score=score)
    elif rule_type == "DEVICE_MISMATCH":
        rule = DeviceMismatchRule(score=score)
    else:
        raise ValueError(f"Unknown rule type '{rule_type}'")

    rule.name = model.name
    rule.description = model.description
    rule.score = score
    return rule


def load_rules_from_db(db: Session) -> List[FraudRule]:
    models = db.scalars(
        select(RuleModel).where(RuleModel.enabled == True).order_by(RuleModel.id)
    ).all()
    return [build_rule_from_model(m) for m in models]
