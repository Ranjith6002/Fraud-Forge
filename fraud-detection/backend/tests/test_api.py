from app.api.deps import get_notifier
from app.main import app
from app.services.notifications import NotificationService
from tests.helpers import api_payload


def post(client, *args, **kwargs):
    return client.post("/api/transactions", json=api_payload(*args, **kwargs))


def build_perfect_fraud(client):
    for i in range(4):  # baseline history on previous days
        assert post(client, f"OLD{i}", user="U999", amount=2000, minutes=-1440 * (i + 1), city="Chennai").status_code == 201
    for i in range(5):  # burst 0..8 minutes
        assert post(client, f"B{i}", user="U999", amount=2000, minutes=i * 2, city="Chennai").status_code == 201
    return post(client, "TX-FRAUD", user="U999", amount=95000, minutes=10, city="London")


def test_health(client):
    body = client.get("/").json()
    assert body["status"] == "ok" and body["database"] == "ok" and body["docs"] == "/docs"


def test_normal_transaction_is_low_risk_and_persisted(client):
    res = post(client, "TX1", amount=1500, city="Chennai")
    assert res.status_code == 201
    body = res.json()
    assert body["risk_score"] == 0 and body["risk_level"] == "LOW" and body["flags"] == []
    assert body["notification_status"] == "NOT_REQUIRED" and body["review_status"] == "PENDING"
    detail = client.get("/api/transactions/TX1").json()
    assert detail["transaction_id"] == "TX1" and detail["amount"] == 1500
    assert client.get("/api/transactions/flagged").json()["total"] == 0


def test_high_risk_transaction_end_to_end(client):
    res = build_perfect_fraud(client)
    body = res.json()
    assert body["risk_score"] == 100 and body["risk_level"] == "HIGH"
    assert {f["rule"] for f in body["flags"]} == {"HIGH_VELOCITY", "UNUSUAL_AMOUNT", "IMPOSSIBLE_GEO"}
    assert {f["rule"]: f["score"] for f in body["flags"]} == {"HIGH_VELOCITY": 30, "UNUSUAL_AMOUNT": 35, "IMPOSSIBLE_GEO": 40}
    # notification was attempted (no AWS configured locally -> SKIPPED, logged)
    assert body["notification_status"] == "SKIPPED"

    detail = client.get("/api/transactions/TX-FRAUD").json()
    assert detail["risk_score"] == 100 and len(detail["rule_results"]) == 3
    assert all(r["triggered"] for r in detail["rule_results"])
    assert client.get("/api/transactions/flagged").json()["items"][0]["transaction_id"] == "TX-FRAUD"


def test_missing_history_and_missing_coordinates_do_not_crash(client):
    res = post(client, "TXNEW", user="BRAND-NEW", amount=9_999_999)  # no history, no coordinates
    assert res.status_code == 201 and res.json()["risk_score"] == 0


def test_duplicate_transaction_id_is_rejected(client):
    assert post(client, "DUP").status_code == 201
    res = post(client, "DUP")
    assert res.status_code == 409


def test_validation_errors(client):
    assert post(client, "BAD1", amount=-5).status_code == 422
    assert post(client, "BAD2", latitude=13.0).status_code == 422  # latitude without longitude
    assert post(client, "BAD3", latitude=123.0, longitude=10.0).status_code == 422
    assert client.post("/api/transactions", json={"transaction_id": "X"}).status_code == 422
    future = api_payload("BAD4")
    future["timestamp"] = "2999-01-01T00:00:00Z"
    assert client.post("/api/transactions", json=future).status_code == 422


def test_invalid_and_tiny_time_intervals_via_api(client):
    assert post(client, "A1", user="U7", minutes=0, city="Chennai").status_code == 201
    res = post(client, "A2", user="U7", minutes=0, city="London")  # same instant, far away
    assert res.status_code == 201
    assert res.json()["risk_score"] == 40 and res.json()["risk_level"] == "MEDIUM"


def test_review_action_persists_status_and_audit_trail(client):
    build_perfect_fraud(client)
    res = client.patch("/api/transactions/TX-FRAUD/review",
                       json={"reviewer": "admin", "comment": "Verified with customer."})
    assert res.status_code == 200
    body = res.json()
    assert body["review_status"] == "REVIEWED"
    assert len(body["flags"]) == 3  # original fraud result preserved
    audit = body["reviews"][0]
    assert audit["reviewer"] == "admin" and audit["previous_status"] == "PENDING"
    assert audit["status"] == "REVIEWED" and audit["comment"] == "Verified with customer."
    assert client.get("/api/transactions/TX-FRAUD").json()["review_status"] == "REVIEWED"


def test_clear_action_keeps_fraud_flags(client):
    build_perfect_fraud(client)
    res = client.patch("/api/transactions/TX-FRAUD/clear",
                       json={"reviewer": "admin", "comment": "Transaction confirmed legitimate."})
    assert res.status_code == 200 and res.json()["review_status"] == "CLEARED"
    detail = client.get("/api/transactions/TX-FRAUD").json()
    assert detail["risk_score"] == 100 and len(detail["flags"]) == 3
    assert client.get("/api/transactions/flagged?status=CLEARED").json()["total"] == 1


def test_review_history_is_appended_and_same_status_is_rejected(client):
    build_perfect_fraud(client)
    client.patch("/api/transactions/TX-FRAUD/review", json={"reviewer": "a"})
    assert client.patch("/api/transactions/TX-FRAUD/review", json={"reviewer": "a"}).status_code == 409
    res = client.patch("/api/transactions/TX-FRAUD/clear", json={"reviewer": "b", "comment": "ok"})
    assert [r["status"] for r in res.json()["reviews"]] == ["REVIEWED", "CLEARED"]
    assert res.json()["reviews"][1]["previous_status"] == "REVIEWED"


def test_review_unknown_transaction_and_missing_reviewer(client):
    assert client.patch("/api/transactions/NOPE/review", json={"reviewer": "a"}).status_code == 404
    assert client.get("/api/transactions/NOPE").status_code == 404
    assert client.patch("/api/transactions/NOPE/clear", json={}).status_code == 422


def test_notification_failure_does_not_crash_transaction_processing(client):
    class Exploding(NotificationService):
        def send_high_risk_alert(self, alert):
            raise RuntimeError("SNS is down")

    app.dependency_overrides[get_notifier] = lambda: Exploding()
    res = build_perfect_fraud(client)
    assert res.status_code == 201
    body = res.json()
    assert body["risk_score"] == 100 and body["notification_status"] == "FAILED"
    assert "SNS is down" in body["notification_detail"]
    assert client.get("/api/transactions/TX-FRAUD").status_code == 200  # still persisted


def test_low_risk_does_not_trigger_notification(client):
    class MustNotBeCalled(NotificationService):
        def send_high_risk_alert(self, alert):
            raise AssertionError("should not notify")

    app.dependency_overrides[get_notifier] = lambda: MustNotBeCalled()
    assert post(client, "SAFE", amount=100).json()["notification_status"] == "NOT_REQUIRED"


def test_filters_search_and_sorting(client):
    build_perfect_fraud(client)
    assert client.get("/api/transactions/flagged?risk_level=HIGH").json()["total"] == 1
    assert client.get("/api/transactions/flagged?risk_level=LOW").json()["total"] == 0
    assert client.get("/api/transactions/flagged?q=u999").json()["total"] >= 1
    assert client.get("/api/transactions/flagged?q=nobody").json()["total"] == 0
    assert client.get("/api/transactions?sort_by=amount&order=desc").json()["items"][0]["transaction_id"] == "TX-FRAUD"
    assert client.get("/api/transactions?risk_level=BOGUS").status_code == 422
    assert client.get("/api/transactions").json()["total"] == 10


def test_dashboard_stats(client):
    build_perfect_fraud(client)
    client.patch("/api/transactions/TX-FRAUD/review", json={"reviewer": "a"})
    post(client, "TXOK", user="U2", amount=100)
    stats = client.get("/api/dashboard/stats").json()
    assert stats["total_transactions"] == 11
    assert stats["flagged_transactions"] >= 1 and stats["high_risk_transactions"] == 1
    assert stats["reviewed_transactions"] == 1 and stats["cleared_transactions"] == 0
    assert stats["pending_reviews"] == stats["flagged_transactions"] - 1
    assert stats["recent_suspicious"][0]["risk_level"] in {"HIGH", "MEDIUM", "LOW"}


def test_seed_creates_the_perfect_demo_fraud(client):
    res = client.post("/api/seed")
    assert res.status_code == 200 and res.json()["created"] > 50
    detail = client.get("/api/transactions/TX-DEMO-FRAUD").json()
    assert detail["risk_score"] == 100 and detail["risk_level"] == "HIGH"
    assert [r["triggered"] for r in detail["rule_results"]] == [True, True, True]
    assert detail["notification_status"] == "SKIPPED"
    # reseeding resets instead of duplicating
    again = client.post("/api/seed").json()
    assert client.get("/api/transactions").json()["total"] == again["created"]
    flagged = client.get("/api/transactions/flagged").json()["items"]
    assert flagged[0]["transaction_id"] == "TX-DEMO-FRAUD"
    levels = {t["risk_level"] for t in flagged}
    assert {"HIGH", "MEDIUM", "LOW"} <= levels


def test_rules_endpoint_lists_registered_rules(client):
    names = [r["name"] for r in client.get("/api/rules").json()]
    assert names == ["HIGH_VELOCITY", "UNUSUAL_AMOUNT", "IMPOSSIBLE_GEO"]
