"""Rule registration = the ONLY place that lists which rules are active.

Adding a rule means adding one line here (or enabling an optional rule via EXTRA_RULES).
`FraudEngine` is never modified.
"""
from typing import Callable, Dict, List

from app.rules.amount import UnusualAmountRule
from app.rules.base import FraudRule
from app.rules.device_mismatch import DeviceMismatchRule
from app.rules.geo import ImpossibleGeoRule
from app.rules.velocity import VelocityRule


def build_default_rules(settings) -> List[FraudRule]:
    """Rules that are always on. `settings` only needs the attributes used below."""
    return [
        VelocityRule(
            max_transactions=settings.velocity_max_transactions,
            window_minutes=settings.velocity_window_minutes,
            score=settings.velocity_score,
        ),
        UnusualAmountRule(
            multiplier=settings.amount_multiplier,
            min_history=settings.amount_min_history,
            score=settings.amount_score,
        ),
        ImpossibleGeoRule(
            max_speed_kmh=settings.geo_max_speed_kmh,
            min_distance_km=settings.geo_min_distance_km,
            score=settings.geo_score,
        ),
    ]


#: Optional rules that can be switched on with EXTRA_RULES=<key>[,<key>]
OPTIONAL_RULES: Dict[str, Callable[[], FraudRule]] = {
    "device_mismatch": lambda: DeviceMismatchRule(),
    # "my_new_rule": lambda: MyNewRule(),
}


def build_rules(settings) -> List[FraudRule]:
    rules = build_default_rules(settings)
    for key in settings.extra_rule_list:
        factory = OPTIONAL_RULES.get(key)
        if factory is None:
            raise ValueError(f"Unknown extra rule '{key}'. Available: {sorted(OPTIONAL_RULES)}")
        rules.append(factory())
    return rules
