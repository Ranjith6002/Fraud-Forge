import os

# Must be set before the app is imported: tests run on an in-memory SQLite database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["NOTIFICATION_PROVIDER"] = "log"
for _key in ("SNS_TOPIC_ARN", "SES_FROM_EMAIL", "ALERT_EMAIL", "EXTRA_RULES"):
    os.environ.pop(_key, None)

import pytest  # noqa: E402


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app import models  # noqa: F401
    from app.api import deps
    from app.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    deps._notifier = None
    yield TestClient(app)
    app.dependency_overrides.clear()
