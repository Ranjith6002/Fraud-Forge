from app.rules import DeviceMismatchRule, ImpossibleGeoRule, UnusualAmountRule, VelocityRule
from app.utils.geo import haversine_km
from tests.helpers import ctx, tx


# ------------------------------------------------------------------ velocity
def test_velocity_triggers_on_sixth_transaction_in_window():
    history = [tx(f"H{i}", minutes=i * 2) for i in range(5)]  # 0,2,4,6,8
    result = VelocityRule().evaluate(tx("NOW", minutes=10), ctx(*history))
    assert result.triggered and result.score == 30 and result.rule_name == "HIGH_VELOCITY"
    assert result.reason == "User made 6 transactions within 10 minutes."


def test_velocity_not_triggered_at_exactly_five():
    history = [tx(f"H{i}", minutes=i * 2) for i in range(4)]  # 4 + current = 5
    assert not VelocityRule().evaluate(tx("NOW", minutes=9), ctx(*history)).triggered


def test_velocity_ignores_transactions_outside_window():
    history = [tx(f"H{i}", minutes=i) for i in range(5)]  # minutes 0..4
    assert not VelocityRule().evaluate(tx("NOW", minutes=30), ctx(*history)).triggered


def test_velocity_thresholds_are_configurable():
    rule = VelocityRule(max_transactions=2, window_minutes=5, score=10)
    result = rule.evaluate(tx("NOW", minutes=2), ctx(tx("A", minutes=0), tx("B", minutes=1)))
    assert result.triggered and result.score == 10


def test_velocity_handles_missing_timestamp_and_first_transaction():
    assert not VelocityRule().evaluate(tx("NOW", timestamp=None), ctx()).triggered
    assert not VelocityRule().evaluate(tx("NOW"), ctx()).triggered


# ------------------------------------------------------------------ amount
def test_amount_rule_triggers_when_far_above_average():
    history = [tx(f"H{i}", amount=a, minutes=-1000 + i) for i, a in enumerate([4000, 4000, 4000, 4000])]
    result = UnusualAmountRule().evaluate(tx("NOW", amount=85000), ctx(*history))
    assert result.triggered and result.score == 35 and result.rule_name == "UNUSUAL_AMOUNT"
    assert "₹85,000" in result.reason and "₹4,000" in result.reason


def test_amount_rule_requires_strictly_more_than_multiplier():
    history = [tx(f"H{i}", amount=1000, minutes=-100 + i) for i in range(4)]
    assert not UnusualAmountRule().evaluate(tx("NOW", amount=5000), ctx(*history)).triggered
    assert UnusualAmountRule().evaluate(tx("NOW", amount=5001), ctx(*history)).triggered


def test_amount_rule_handles_missing_history_gracefully():
    result = UnusualAmountRule().evaluate(tx("NOW", amount=999999), ctx())
    assert not result.triggered and "Not enough history" in result.reason


def test_amount_rule_needs_minimum_history():
    history = [tx("H1", amount=100, minutes=-10), tx("H2", amount=100, minutes=-5)]
    assert not UnusualAmountRule().evaluate(tx("NOW", amount=100000), ctx(*history)).triggered
    assert UnusualAmountRule(min_history=2).evaluate(tx("NOW", amount=100000), ctx(*history)).triggered


def test_amount_rule_ignores_invalid_historical_amounts():
    history = [tx("H1", amount=0, minutes=-10), tx("H2", amount=-5, minutes=-9), tx("H3", amount=100, minutes=-8)]
    result = UnusualAmountRule(min_history=1).evaluate(tx("NOW", amount=1000), ctx(*history))
    assert result.triggered and result.details["history_count"] == 1


# ------------------------------------------------------------------ geo
def test_geo_rule_flags_chennai_to_london_in_15_minutes():
    prev = tx("P", city="Chennai", minutes=0)
    result = ImpossibleGeoRule().evaluate(tx("NOW", city="London", minutes=15), ctx(prev))
    assert result.triggered and result.score == 40 and result.rule_name == "IMPOSSIBLE_GEO"
    assert result.details["required_speed_kmh"] > 900
    assert "Chennai" in result.reason and "London" in result.reason


def test_geo_rule_allows_plausible_travel():
    prev = tx("P", city="Chennai", minutes=0)
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="Bengaluru", minutes=360), ctx(prev)).triggered


def test_geo_rule_first_transaction_is_not_flagged():
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="London"), ctx()).triggered


def test_geo_rule_missing_coordinates_do_not_crash():
    prev = tx("P", city="Chennai", minutes=0)
    assert not ImpossibleGeoRule().evaluate(tx("NOW", minutes=5), ctx(prev)).triggered  # current has none
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="London", minutes=5), ctx(tx("P2", minutes=0))).triggered


def test_geo_rule_skips_previous_transactions_without_coordinates():
    located = tx("A", city="Chennai", minutes=0)
    unlocated = tx("B", minutes=5)
    result = ImpossibleGeoRule().evaluate(tx("NOW", city="London", minutes=10), ctx(located, unlocated))
    assert result.triggered and result.details["previous_transaction_id"] == "A"


def test_geo_rule_identical_location_is_fine():
    prev = tx("P", city="Chennai", minutes=0)
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="Chennai", minutes=0), ctx(prev)).triggered


def test_geo_rule_zero_elapsed_time_does_not_divide_by_zero():
    prev = tx("P", city="Chennai", minutes=0)
    result = ImpossibleGeoRule().evaluate(tx("NOW", city="London", minutes=0), ctx(prev))
    assert result.triggered  # far apart at the same instant is impossible


def test_geo_rule_very_small_time_difference_between_far_cities():
    prev = tx("P", city="Chennai", minutes=0)
    now = tx("NOW", city="Mumbai", minutes=1 / 60)  # one second later
    assert ImpossibleGeoRule().evaluate(now, ctx(prev)).triggered


def test_geo_rule_ignores_future_history_and_invalid_timestamp():
    future = tx("F", city="Chennai", minutes=60)
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="London", minutes=0), ctx(future)).triggered
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="London", timestamp=None), ctx(future)).triggered
    bad_prev = tx("BAD", city="Chennai", timestamp=None)
    assert not ImpossibleGeoRule().evaluate(tx("NOW", city="London", minutes=5), ctx(bad_prev)).triggered


def test_geo_rule_invalid_coordinates_are_treated_as_missing():
    bad = tx("NOW", minutes=5, city=None)
    bad = type(bad)(**{**bad.__dict__, "latitude": 999.0, "longitude": 10.0})
    assert not ImpossibleGeoRule().evaluate(bad, ctx(tx("P", city="Chennai"))).triggered


def test_haversine_distance_is_accurate():
    assert abs(haversine_km(13.0827, 80.2707, 51.5074, -0.1278) - 8211) < 60
    assert haversine_km(10, 10, 10, 10) == 0


# ------------------------------------------------------------------ device (example extra rule)
def test_device_mismatch_rule():
    known = [tx("A", device="phone-1", minutes=-10)]
    assert DeviceMismatchRule().evaluate(tx("NOW", device="laptop-9"), ctx(*known)).triggered
    assert not DeviceMismatchRule().evaluate(tx("NOW", device="phone-1"), ctx(*known)).triggered
    assert not DeviceMismatchRule().evaluate(tx("NOW", device="laptop-9"), ctx()).triggered
    assert not DeviceMismatchRule().evaluate(tx("NOW"), ctx(*known)).triggered
