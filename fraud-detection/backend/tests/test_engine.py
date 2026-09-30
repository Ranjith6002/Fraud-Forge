import pytest

from app.domain import RiskLevel, RuleResult
from app.engine import FraudEngine, RiskThresholds
from app.rules import DeviceMismatchRule, FraudRule, ImpossibleGeoRule, UnusualAmountRule, VelocityRule
from tests.helpers import ctx, tx


def default_engine():
    return FraudEngine([VelocityRule(), UnusualAmountRule(), ImpossibleGeoRule()])


def perfect_fraud_history():
    history = [tx(f"OLD{i}", amount=2000, city="Chennai", minutes=-1440 * (i + 1)) for i in range(4)]
    history += [tx(f"B{i}", amount=2000, city="Chennai", minutes=i * 2) for i in range(5)]  # 0..8
    return history


def test_normal_transaction_scores_zero():
    result = default_engine().evaluate(tx("NOW", amount=1500, city="Chennai"), ctx())
    assert result.risk_score == 0 and result.risk_level == RiskLevel.LOW and not result.is_flagged
    assert len(result.results) == 3  # every registered rule reports, triggered or not


def test_high_risk_transaction_aggregates_all_rules_and_caps_at_100():
    result = default_engine().evaluate(tx("NOW", amount=95000, city="London", minutes=10),
                                       ctx(*perfect_fraud_history()))
    assert {f.rule_name for f in result.flags} == {"HIGH_VELOCITY", "UNUSUAL_AMOUNT", "IMPOSSIBLE_GEO"}
    assert result.raw_score == 105
    assert result.risk_score == 100
    assert result.risk_level == RiskLevel.HIGH


def test_partial_aggregation_of_two_rules():
    history = [tx(f"H{i}", amount=4000, city="Chennai", minutes=-500 + i) for i in range(4)]
    result = default_engine().evaluate(tx("NOW", amount=85000, city="London", minutes=-480), ctx(*history))
    assert result.risk_score == 75 and result.risk_level == RiskLevel.HIGH  # amount 35 + geo 40


def test_risk_level_boundaries():
    t = RiskThresholds()
    assert t.level_for(0) == RiskLevel.LOW
    assert t.level_for(39) == RiskLevel.LOW
    assert t.level_for(40) == RiskLevel.MEDIUM
    assert t.level_for(69) == RiskLevel.MEDIUM
    assert t.level_for(70) == RiskLevel.HIGH
    assert t.level_for(100) == RiskLevel.HIGH


def test_risk_thresholds_are_configurable_and_validated():
    custom = RiskThresholds(medium=20, high=50)
    assert custom.level_for(25) == RiskLevel.MEDIUM and custom.level_for(50) == RiskLevel.HIGH
    with pytest.raises(ValueError):
        RiskThresholds(medium=80, high=70)


def test_score_is_capped_by_configured_max():
    class Big(FraudRule):
        name = "BIG"

        def evaluate(self, transaction, context):
            return self.hit("big")

    assert FraudEngine([Big(score=80)]).evaluate(tx("X"), ctx()).risk_score == 80

    class Other(Big):
        name = "OTHER"

    engine = FraudEngine([Big(score=80), Other(score=80)])
    assessment = engine.evaluate(tx("X"), ctx())
    assert assessment.raw_score == 160 and assessment.risk_score == 100


def test_new_rule_can_be_added_without_modifying_the_engine():
    """Key extensibility check: the engine class is untouched; we just pass another rule."""
    history = [tx("A", device="phone-1", minutes=-30)]
    base = default_engine().evaluate(tx("NOW", device="laptop-9"), ctx(*history))
    assert base.risk_score == 0

    extended = FraudEngine([VelocityRule(), UnusualAmountRule(), ImpossibleGeoRule(), DeviceMismatchRule()])
    result = extended.evaluate(tx("NOW", device="laptop-9"), ctx(*history))
    assert [f.rule_name for f in result.flags] == ["DEVICE_MISMATCH"]
    assert result.risk_score == 25


def test_engine_can_register_rules_at_runtime_and_rejects_duplicates():
    engine = default_engine()
    engine.register(DeviceMismatchRule())
    assert [r.name for r in engine.rules][-1] == "DEVICE_MISMATCH"
    with pytest.raises(ValueError):
        engine.register(DeviceMismatchRule())


def test_a_crashing_rule_does_not_break_evaluation():
    class Boom(FraudRule):
        name = "BOOM"

        def evaluate(self, transaction, context):
            raise RuntimeError("kaput")

    engine = FraudEngine([Boom(score=50), VelocityRule()])
    result = engine.evaluate(tx("X"), ctx())
    assert result.risk_score == 0
    boom = [r for r in result.results if r.rule_name == "BOOM"][0]
    assert not boom.triggered and "kaput" in boom.reason


def test_non_triggered_results_never_contribute_score():
    class Sneaky(FraudRule):
        name = "SNEAKY"

        def evaluate(self, transaction, context):
            return RuleResult(self.name, False, 99, "nope")

    result = FraudEngine([Sneaky(score=99)]).evaluate(tx("X"), ctx())
    assert result.risk_score == 0
