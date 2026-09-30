"""Notification abstraction. The FraudEngine never sees this; TransactionService does.

FraudEngine -> TransactionService -> NotificationService -> (SNS | SES | log)
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.utils.formatting import format_money

logger = logging.getLogger(__name__)

SENT, FAILED, SKIPPED = "SENT", "FAILED", "SKIPPED"


@dataclass
class HighRiskAlert:
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    location: Optional[str]
    risk_score: int
    risk_level: str
    reasons: List[str] = field(default_factory=list)
    console_url: str = ""

    @property
    def subject(self) -> str:
        return f"[Fraud Alert] {self.risk_level} risk transaction {self.transaction_id} (score {self.risk_score})"

    @property
    def body(self) -> str:
        lines = [
            f"Transaction: {self.transaction_id}",
            f"User: {self.user_id}",
            f"Amount: {format_money(self.amount, self.currency)}",
            f"Location: {self.location or 'unknown'}",
            f"Risk: {self.risk_level} ({self.risk_score}/100)",
            "",
            "Why it was flagged:",
            *[f" - {r}" for r in self.reasons],
        ]
        if self.console_url:
            lines += ["", f"Review it: {self.console_url}/transactions/{self.transaction_id}"]
        return "\n".join(lines)


@dataclass
class NotificationResult:
    status: str  # SENT | FAILED | SKIPPED
    detail: str = ""


class NotificationService(ABC):
    @abstractmethod
    def send_high_risk_alert(self, alert: HighRiskAlert) -> NotificationResult: ...


class LoggingNotificationService(NotificationService):
    """Used when no AWS channel is configured: the attempt is logged, nothing is sent."""

    def __init__(self, reason: str = "No AWS notification channel configured; alert logged locally only.") -> None:
        self.reason = reason

    def send_high_risk_alert(self, alert: HighRiskAlert) -> NotificationResult:
        return NotificationResult(SKIPPED, self.reason)


class _AwsBase(NotificationService):
    def __init__(self, region, access_key, secret_key, client=None) -> None:
        self.region, self.access_key, self.secret_key = region, access_key, secret_key
        self._client = client

    def _make_client(self, service: str) -> Any:
        if self._client is None:
            import boto3
            from botocore.config import Config

            kwargs = {
                "region_name": self.region,
                "config": Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1}),
            }
            if self.access_key and self.secret_key:
                kwargs["aws_access_key_id"] = self.access_key
                kwargs["aws_secret_access_key"] = self.secret_key
            self._client = boto3.client(service, **kwargs)
        return self._client


class SNSNotificationService(_AwsBase):
    def __init__(self, topic_arn, region=None, access_key=None, secret_key=None, client=None) -> None:
        super().__init__(region, access_key, secret_key, client)
        self.topic_arn = topic_arn

    def send_high_risk_alert(self, alert: HighRiskAlert) -> NotificationResult:
        if not self.topic_arn:
            return NotificationResult(SKIPPED, "SNS skipped: SNS_TOPIC_ARN not configured.")
        try:
            resp = self._make_client("sns").publish(
                TopicArn=self.topic_arn, Subject=alert.subject[:100], Message=alert.body
            )
            return NotificationResult(SENT, f"SNS message {resp.get('MessageId', '')}".strip())
        except Exception as exc:
            logger.warning("SNS publish failed: %s", exc)
            return NotificationResult(FAILED, f"SNS failed: {exc}")


class SESNotificationService(_AwsBase):
    def __init__(self, from_email, to_emails, region=None, access_key=None, secret_key=None, client=None) -> None:
        super().__init__(region, access_key, secret_key, client)
        self.from_email = from_email
        self.to_emails = [e.strip() for e in (to_emails or "").split(",") if e.strip()]

    def send_high_risk_alert(self, alert: HighRiskAlert) -> NotificationResult:
        if not (self.from_email and self.to_emails):
            return NotificationResult(SKIPPED, "SES skipped: SES_FROM_EMAIL / ALERT_EMAIL not configured.")
        try:
            resp = self._make_client("ses").send_email(
                Source=self.from_email,
                Destination={"ToAddresses": self.to_emails},
                Message={
                    "Subject": {"Data": alert.subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": alert.body, "Charset": "UTF-8"}},
                },
            )
            return NotificationResult(SENT, f"SES message {resp.get('MessageId', '')}".strip())
        except Exception as exc:
            logger.warning("SES send failed: %s", exc)
            return NotificationResult(FAILED, f"SES failed: {exc}")


class CompositeNotificationService(NotificationService):
    def __init__(self, services: List[NotificationService]) -> None:
        self.services = services

    def send_high_risk_alert(self, alert: HighRiskAlert) -> NotificationResult:
        results = []
        for svc in self.services:
            try:
                results.append(svc.send_high_risk_alert(alert))
            except Exception as exc:  # defensive: a channel must never raise
                results.append(NotificationResult(FAILED, f"{type(svc).__name__} failed: {exc}"))
        detail = " | ".join(r.detail for r in results if r.detail)
        if any(r.status == SENT for r in results):
            return NotificationResult(SENT, detail)
        if any(r.status == FAILED for r in results):
            return NotificationResult(FAILED, detail)
        return NotificationResult(SKIPPED, detail)


def build_notifier(settings) -> NotificationService:
    provider = (settings.notification_provider or "auto").lower()
    common = dict(region=settings.aws_region, access_key=settings.aws_access_key_id,
                  secret_key=settings.aws_secret_access_key)
    sns = SNSNotificationService(settings.sns_topic_arn, **common)
    ses = SESNotificationService(settings.ses_from_email, settings.alert_email, **common)

    if provider == "none":
        return LoggingNotificationService("Notifications are disabled (NOTIFICATION_PROVIDER=none).")
    if provider == "log":
        return LoggingNotificationService()
    if provider == "sns":
        return sns
    if provider == "ses":
        return ses
    if provider == "both":
        return CompositeNotificationService([sns, ses])
    channels: List[NotificationService] = []  # auto: use whatever is configured
    if settings.sns_topic_arn:
        channels.append(sns)
    if settings.ses_from_email and settings.alert_email:
        channels.append(ses)
    return CompositeNotificationService(channels) if channels else LoggingNotificationService()


def dispatch_alert(notifier: NotificationService, alert: HighRiskAlert) -> NotificationResult:
    """Send an alert; NEVER raises, so a notification problem cannot fail a transaction."""
    logger.warning(
        "High-risk transaction detected",
        extra={"transaction_id": alert.transaction_id, "risk_score": alert.risk_score, "user_id": alert.user_id},
    )
    try:
        return notifier.send_high_risk_alert(alert)
    except Exception as exc:
        logger.exception("Notification failed", extra={"transaction_id": alert.transaction_id})
        return NotificationResult(FAILED, f"Notification failed: {exc}")
