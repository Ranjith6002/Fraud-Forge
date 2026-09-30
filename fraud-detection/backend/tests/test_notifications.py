from app.services.notifications import (
    FAILED, SENT, SKIPPED, HighRiskAlert, LoggingNotificationService, NotificationService,
    SESNotificationService, SNSNotificationService, build_notifier, dispatch_alert,
)
from types import SimpleNamespace

ALERT = HighRiskAlert("TX1", "U1", 95000, "INR", "London", 100, "HIGH", ["reason one", "reason two"],
                      "http://localhost:5173")


class FakeSNS:
    def __init__(self):
        self.calls = []

    def publish(self, **kwargs):
        self.calls.append(kwargs)
        return {"MessageId": "abc-123"}


class FakeSES:
    def __init__(self):
        self.calls = []

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        return {"MessageId": "ses-1"}


class BrokenClient:
    def publish(self, **kwargs):
        raise RuntimeError("no credentials")

    send_email = publish


def settings(**over):
    base = dict(notification_provider="auto", sns_topic_arn=None, ses_from_email=None, alert_email=None,
                aws_region=None, aws_access_key_id=None, aws_secret_access_key=None)
    base.update(over)
    return SimpleNamespace(**base)


def test_alert_body_contains_reasons_and_link():
    assert "reason one" in ALERT.body and "/transactions/TX1" in ALERT.body and "TX1" in ALERT.subject


def test_unconfigured_notifier_is_skipped_not_failed():
    result = dispatch_alert(build_notifier(settings()), ALERT)
    assert result.status == SKIPPED and "logged locally" in result.detail


def test_sns_publishes_when_configured():
    fake = FakeSNS()
    result = SNSNotificationService("arn:aws:sns:ap-south-1:123:alerts", client=fake).send_high_risk_alert(ALERT)
    assert result.status == SENT and "abc-123" in result.detail
    assert fake.calls[0]["TopicArn"].startswith("arn:aws:sns")


def test_ses_sends_email_when_configured():
    fake = FakeSES()
    svc = SESNotificationService("from@example.com", "a@example.com, b@example.com", client=fake)
    assert svc.send_high_risk_alert(ALERT).status == SENT
    assert fake.calls[0]["Destination"]["ToAddresses"] == ["a@example.com", "b@example.com"]


def test_sns_and_ses_without_config_are_skipped():
    assert SNSNotificationService(None).send_high_risk_alert(ALERT).status == SKIPPED
    assert SESNotificationService(None, None).send_high_risk_alert(ALERT).status == SKIPPED


def test_aws_errors_become_failed_results_not_exceptions():
    assert SNSNotificationService("arn", client=BrokenClient()).send_high_risk_alert(ALERT).status == FAILED
    assert SESNotificationService("f@x.com", "t@x.com", client=BrokenClient()).send_high_risk_alert(ALERT).status == FAILED


def test_dispatch_alert_never_raises():
    class Exploding(NotificationService):
        def send_high_risk_alert(self, alert):
            raise Exception("boom")

    result = dispatch_alert(Exploding(), ALERT)
    assert result.status == FAILED and "boom" in result.detail


def test_provider_selection():
    assert isinstance(build_notifier(settings(notification_provider="log")), LoggingNotificationService)
    assert isinstance(build_notifier(settings(notification_provider="sns", sns_topic_arn="arn")), SNSNotificationService)
    assert isinstance(build_notifier(settings(notification_provider="none")), LoggingNotificationService)
