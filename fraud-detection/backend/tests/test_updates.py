import pytest
from tests.helpers import api_payload


def post(client, *args, **kwargs):
    return client.post("/api/transactions", json=api_payload(*args, **kwargs))


def test_submit_transaction_with_location_success(client):
    """TEST 1: Submit transaction with location returns success."""
    payload = api_payload("TX_LOC_OK", user="U_LOC1", amount=1500, city="Chennai")
    res = client.post("/api/transactions", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["transaction_id"] == "TX_LOC_OK"


def test_submit_transaction_without_location_backend_validation_error(client):
    """TEST 2 & 3: Direct API request without location or empty whitespace returns 422 error."""
    # Missing location key
    payload_missing = api_payload("TX_NO_LOC", city=None)
    payload_missing.pop("location", None)
    res1 = client.post("/api/transactions", json=payload_missing)
    assert res1.status_code == 422

    # Whitespace location
    payload_space = api_payload("TX_SPACE_LOC", city="   ")
    res2 = client.post("/api/transactions", json=payload_space)
    assert res2.status_code == 422


def test_create_valid_new_fraud_rule(client):
    """TEST 4: Create a valid new fraud rule via API and verify persistence."""
    rule_data = {
        "name": "CUSTOM_VELOCITY_FAST",
        "rule_type": "VELOCITY",
        "description": "Flags 3+ transactions within 5 minutes.",
        "enabled": True,
        "risk_score": 25,
        "parameters": {"max_transactions": 2, "window_minutes": 5},
    }
    res = client.post("/api/rules", json=rule_data)
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "CUSTOM_VELOCITY_FAST"
    assert body["enabled"] is True
    assert body["risk_score"] == 25

    # Verify listing includes the new rule
    rules = client.get("/api/rules").json()
    assert any(r["name"] == "CUSTOM_VELOCITY_FAST" for r in rules)


def test_create_invalid_rule_configuration(client):
    """TEST 5: Create invalid rule configuration returns validation error."""
    bad_rule = {
        "name": "INVALID_RULE",
        "rule_type": "VELOCITY",
        "description": "Invalid negative window",
        "enabled": True,
        "risk_score": 25,
        "parameters": {"max_transactions": 0, "window_minutes": -5},
    }
    res = client.post("/api/rules", json=bad_rule)
    assert res.status_code == 422


def test_new_enabled_rule_evaluates_and_triggers_transaction(client):
    """TEST 6: Create new enabled rule and submit transaction that satisfies it -> triggers."""
    # Create rule: VELOCITY limit max 2 transactions in 10 minutes
    client.post(
        "/api/rules",
        json={
            "name": "STRICT_VELOCITY",
            "rule_type": "VELOCITY",
            "description": "Max 2 txns per 10 mins",
            "enabled": True,
            "risk_score": 30,
            "parameters": {"max_transactions": 2, "window_minutes": 10},
        },
    )

    # Submit 3 transactions in short interval for user U_DYNAMIC
    client.post("/api/transactions", json=api_payload("TX_D1", user="U_DYNAMIC", minutes=0, city="Chennai"))
    client.post("/api/transactions", json=api_payload("TX_D2", user="U_DYNAMIC", minutes=2, city="Chennai"))
    res3 = client.post("/api/transactions", json=api_payload("TX_D3", user="U_DYNAMIC", minutes=4, city="Chennai"))

    assert res3.status_code == 201
    body = res3.json()
    flag_names = [f["rule"] for f in body["flags"]]
    assert "STRICT_VELOCITY" in flag_names


def test_disabled_rule_does_not_trigger(client):
    """TEST 7: Create a new disabled rule and verify it does NOT trigger."""
    client.post(
        "/api/rules",
        json={
            "name": "DISABLED_VELOCITY",
            "rule_type": "VELOCITY",
            "description": "Max 1 txn per 10 mins",
            "enabled": False,
            "risk_score": 30,
            "parameters": {"max_transactions": 1, "window_minutes": 10},
        },
    )

    client.post("/api/transactions", json=api_payload("TX_OFF1", user="U_OFF", minutes=0, city="Chennai"))
    res2 = client.post("/api/transactions", json=api_payload("TX_OFF2", user="U_OFF", minutes=2, city="Chennai"))

    assert res2.status_code == 201
    flag_names = [f["rule"] for f in res2.json()["flags"]]
    assert "DISABLED_VELOCITY" not in flag_names


def test_enabling_rule_causes_it_to_trigger_on_future_transactions(client):
    """TEST 8: Enable a disabled rule via PATCH and verify future transactions trigger it."""
    res_create = client.post(
        "/api/rules",
        json={
            "name": "TOGGLE_RULE",
            "rule_type": "VELOCITY",
            "description": "Max 1 txn in 10 mins",
            "enabled": False,
            "risk_score": 20,
            "parameters": {"max_transactions": 1, "window_minutes": 10},
        },
    )
    rule_id = res_create.json()["id"]

    # Toggle enabled to True
    res_patch = client.patch(f"/api/rules/{rule_id}", json={"enabled": True})
    assert res_patch.status_code == 200 and res_patch.json()["enabled"] is True

    # Submit transaction
    client.post("/api/transactions", json=api_payload("TX_TOG1", user="U_TOG", minutes=0, city="Chennai"))
    res2 = client.post("/api/transactions", json=api_payload("TX_TOG2", user="U_TOG", minutes=2, city="Chennai"))

    assert res2.status_code == 201
    flag_names = [f["rule"] for f in res2.json()["flags"]]
    assert "TOGGLE_RULE" in flag_names


def test_triggered_dynamic_rule_appears_in_explanation(client):
    """TEST 9: Triggered dynamic rule appears in transaction details explanation."""
    client.post(
        "/api/rules",
        json={
            "name": "EXPLAIN_RULE",
            "rule_type": "VELOCITY",
            "description": "Max 1 txn per 10 mins",
            "enabled": True,
            "risk_score": 25,
            "parameters": {"max_transactions": 1, "window_minutes": 10},
        },
    )

    client.post("/api/transactions", json=api_payload("TX_EXP1", user="U_EXP", minutes=0, city="Chennai"))
    client.post("/api/transactions", json=api_payload("TX_EXP2", user="U_EXP", minutes=1, city="Chennai"))

    detail = client.get("/api/transactions/TX_EXP2").json()
    rule_names = [r["rule"] for r in detail["rule_results"] if r["triggered"]]
    assert "EXPLAIN_RULE" in rule_names


def test_risk_score_includes_dynamic_rule_contribution(client):
    """TEST 10: Risk score includes dynamic rule risk score contribution."""
    client.post(
        "/api/rules",
        json={
            "name": "HIGH_SCORE_RULE",
            "rule_type": "VELOCITY",
            "description": "Max 1 txn per 10 mins",
            "enabled": True,
            "risk_score": 45,
            "parameters": {"max_transactions": 1, "window_minutes": 10},
        },
    )

    client.post("/api/transactions", json=api_payload("TX_SC1", user="U_SC", minutes=0, city="Chennai"))
    res2 = client.post("/api/transactions", json=api_payload("TX_SC2", user="U_SC", minutes=1, city="Chennai"))

    body = res2.json()
    assert body["risk_score"] >= 45


def test_existing_velocity_rule_still_works(client):
    """TEST 11: Verify existing Velocity rule still works."""
    for i in range(5):
        client.post("/api/transactions", json=api_payload(f"TX_V_{i}", user="U_VEL", minutes=i, city="Chennai"))
    res = client.post("/api/transactions", json=api_payload("TX_V_BURST", user="U_VEL", minutes=6, city="Chennai"))
    flag_names = [f["rule"] for f in res.json()["flags"]]
    assert "HIGH_VELOCITY" in flag_names


def test_existing_amount_rule_still_works(client):
    """TEST 12: Verify existing Amount rule still works."""
    for i in range(4):
        client.post("/api/transactions", json=api_payload(f"TX_A_{i}", user="U_AMT", amount=1000, minutes=-100 + i, city="Chennai"))
    res = client.post("/api/transactions", json=api_payload("TX_A_BIG", user="U_AMT", amount=50000, minutes=0, city="Chennai"))
    flag_names = [f["rule"] for f in res.json()["flags"]]
    assert "UNUSUAL_AMOUNT" in flag_names


def test_existing_geo_rule_still_works(client):
    """TEST 13: Verify existing Geo rule still works."""
    client.post("/api/transactions", json=api_payload("TX_G1", user="U_GEO", minutes=0, city="Chennai"))
    res = client.post("/api/transactions", json=api_payload("TX_G2", user="U_GEO", minutes=10, city="London"))
    flag_names = [f["rule"] for f in res.json()["flags"]]
    assert "IMPOSSIBLE_GEO" in flag_names


def test_existing_transaction_review_and_clear_functionality(client):
    """TEST 14: Verify review and clear functionality still works."""
    client.post("/api/transactions", json=api_payload("TX_REV1", user="U_REV", amount=1000, city="Chennai"))
    res_review = client.patch("/api/transactions/TX_REV1/review", json={"reviewer": "analyst1", "comment": "Verified"})
    assert res_review.status_code == 200 and res_review.json()["review_status"] == "REVIEWED"

    res_clear = client.patch("/api/transactions/TX_REV1/clear", json={"reviewer": "analyst2", "comment": "Cleared"})
    assert res_clear.status_code == 200 and res_clear.json()["review_status"] == "CLEARED"
