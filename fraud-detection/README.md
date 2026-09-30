# Fraud Rule Engine with Review Console

A pluggable fraud-detection engine (FastAPI + PostgreSQL) with a React reviewer console.
Transactions are scored by independent rules; risky ones are flagged, alerted via AWS SNS/SES,
and investigated by reviewers who mark them **Reviewed** or **Cleared** with a full audit trail.

## Features
- Plugin-style rule engine: `FraudEngine(rules)` has **no knowledge of individual rules**.
- Three rules: **HIGH_VELOCITY** (+30), **UNUSUAL_AMOUNT** (+35), **IMPOSSIBLE_GEO** (+40, Haversine).
- Risk score (capped at 100) → LOW / MEDIUM / HIGH, all thresholds configurable via env vars.
- Persisted transactions, fraud flags, and an append-only review/audit table.
- High-risk (`score >= 70`) alerts through a notification abstraction (SNS and/or SES); failures never break a transaction.
- Reviewer console: dashboard, flagged list (search/filter/sort), transaction details ("why was this flagged?"), review/clear with confirmation, audit trail, live transaction form.
- One-click demo data including a "perfect fraud" transaction (`TX-DEMO-FRAUD`, score 100).

## Architecture
```
React (Vite + Tailwind) ──REST──► FastAPI ──► PostgreSQL
                                     │
                       TransactionService
                        │        │        │
                 FraudEngine  Persistence  NotificationService ──► SNS / SES / log
                        │
        ┌───────────────┼────────────────┐
  VelocityRule    UnusualAmountRule   ImpossibleGeoRule   (+ any FraudRule you add)
```
Flow: validate → persist → build history context → run all registered rules → sum & cap score →
level → persist flags → notify if high risk → return evaluation → reviewer acts → audit row.

## Tech stack
Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 16, Pydantic v2, boto3, pytest · React 18, Vite, Tailwind CSS 3 · Docker Compose.

## Folder structure
```
backend/app/
  main.py, config.py, database.py, domain.py
  rules/      base.py (FraudRule), velocity.py, amount.py, geo.py, device_mismatch.py (example), registry.py
  engine/     fraud_engine.py, scoring.py
  services/   transaction_service, review_service, query_service, seed_service/seed_data, notifications
  models/     transaction, fraud_flag, review          schemas/  Pydantic models
  api/        transactions.py, dashboard.py, deps.py, serializers.py      utils/  geo, formatting, logging
backend/tests/   pytest suite
frontend/src/    pages/ components/ services/ hooks/ utils/
docker-compose.yml  .env.example
```

## Run with Docker (recommended)
```bash
cp .env.example .env        # optional; only needed for AWS settings
docker compose up --build
```
- Console: http://localhost:5173
- API: http://localhost:8000 · Swagger: http://localhost:8000/docs

Tables are created automatically on backend start (it waits for PostgreSQL).

## Run locally without Docker
PostgreSQL:
```bash
docker run -d --name fraud-pg -e POSTGRES_USER=fraud -e POSTGRES_PASSWORD=fraud -e POSTGRES_DB=fraud -p 5432:5432 postgres:16-alpine
```
Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```
Frontend:
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (set VITE_API_URL if the API is elsewhere)
npm run build        # production build
```

## Environment variables
| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL (`postgresql+psycopg2://user:pass@host:5432/db`) |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS credentials (omit to use the default AWS credential chain / IAM role) |
| `SNS_TOPIC_ARN` | SNS topic for alerts |
| `SES_FROM_EMAIL`, `ALERT_EMAIL` | Verified SES sender and recipient(s) (comma-separated) |
| `NOTIFICATION_PROVIDER` | `auto` (default), `sns`, `ses`, `both`, `log`, `none` |
| `EXTRA_RULES` | Optional rules to enable, e.g. `device_mismatch` |
| `VELOCITY_*`, `AMOUNT_*`, `GEO_*`, `RISK_*_THRESHOLD`, `NOTIFY_THRESHOLD` | Override rule/score thresholds (see `app/config.py`) |

## AWS setup
**SNS:** create a topic, subscribe an email/SMS endpoint (confirm the subscription), set `SNS_TOPIC_ARN`. The IAM identity needs `sns:Publish`.
**SES:** verify the sender (and recipient while in the SES sandbox), set `SES_FROM_EMAIL` and `ALERT_EMAIL`. IAM needs `ses:SendEmail`.
If nothing is configured the alert is **logged** and the transaction is marked `notification_status = SKIPPED`;
if AWS errors, it is marked `FAILED` — the request still succeeds. The console shows the outcome.

## API
Swagger UI: `/docs`.

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health/status |
| POST | `/api/transactions` | Create + evaluate (201; 409 duplicate id; 422 invalid) |
| GET | `/api/transactions` | List (`q`, `risk_level`, `status`, `sort_by`, `order`, `limit`, `offset`) |
| GET | `/api/transactions/flagged` | Flagged only (same filters) |
| GET | `/api/transactions/{id}` | Details: flags, per-rule results, notification, audit trail |
| PATCH | `/api/transactions/{id}/review` | Mark REVIEWED `{reviewer, comment}` |
| PATCH | `/api/transactions/{id}/clear` | Mark CLEARED `{reviewer, comment}` |
| GET | `/api/dashboard/stats` | Dashboard counters + recent suspicious |
| GET | `/api/rules` | Registered rules and their parameters |
| POST | `/api/seed` | Reset and load demo data (`?reset=false` to append) |

Example:
```bash
curl -X POST localhost:8000/api/transactions -H 'Content-Type: application/json' -d '{
  "transaction_id": "TX5001", "user_id": "U42", "amount": 85000, "currency": "INR",
  "merchant": "Luxury Jewellers", "latitude": 51.5074, "longitude": -0.1278, "location": "London"
}'
# -> {"transaction_id":"TX5001","risk_score":..,"risk_level":"..","flags":[{"rule":"..","score":..,"reason":".."}], ...}

curl -X PATCH localhost:8000/api/transactions/TX-DEMO-FRAUD/review -H 'Content-Type: application/json' \
  -d '{"reviewer":"admin","comment":"Verified with customer."}'
```

## How the rules work
| Rule | Triggers when | Default |
|---|---|---|
| `HIGH_VELOCITY` | > 5 transactions by the same user within 10 minutes (including the current one) | +30 |
| `UNUSUAL_AMOUNT` | amount > 5 × the user's historical average (needs ≥ 3 prior transactions) | +35 |
| `IMPOSSIBLE_GEO` | Haversine distance to the previous located transaction ÷ elapsed time > 900 km/h (ignores < 50 km GPS jitter) | +40 |

Edge cases handled without errors: first transaction, no history, missing/invalid coordinates or timestamps,
identical locations, zero/tiny time gaps (elapsed time is floored at 1 second), out-of-order history.

## How risk scoring works
`score = min(sum(triggered rule scores), 100)`. LOW 0–39 · MEDIUM 40–69 · HIGH 70–100 (configurable).
Scores ≥ 70 send an alert. A broken rule is logged and scored as "not triggered" so it cannot break evaluation.

## Adding a new rule (no engine changes)
1. Create the rule (this repo ships a working example: `backend/app/rules/device_mismatch.py`):
```python
from app.rules.base import FraudRule

class DeviceMismatchRule(FraudRule):
    name = "DEVICE_MISMATCH"
    description = "Transaction made from a device the user has never used."

    def __init__(self, score: int = 25):
        super().__init__(score)

    def evaluate(self, transaction, context):
        known = {h.device_id for h in context.history_before(transaction) if h.device_id}
        if transaction.device_id and known and transaction.device_id not in known:
            return self.hit(f"Device '{transaction.device_id}' has not been used by this user before.")
        return self.miss()
```
2. Register it in `backend/app/rules/registry.py` (one line in `OPTIONAL_RULES`, or append to `build_default_rules`).
3. Restart. **`FraudEngine` is not modified** — it just iterates whatever rules it is given:
```python
engine = FraudEngine([VelocityRule(), UnusualAmountRule(), ImpossibleGeoRule(), DeviceMismatchRule()])
```
**Live demo:** `EXTRA_RULES=device_mismatch docker compose up -d --build backend`, then
`GET /api/rules` lists 4 rules and the console's rule cards / "why flagged" panel show `DEVICE_MISMATCH`
(submit a transaction with a new `Device ID` from the *Submit Transaction* page after a first one with another device).
`tests/test_engine.py::test_new_rule_can_be_added_without_modifying_the_engine` proves the same in code.

## Seeding demo data
Click **Seed Demo Data** on the dashboard, or `curl -X POST localhost:8000/api/seed`. It resets the tables and loads ~100
transactions: normal users, a legitimate Delhi→Mumbai trip (not flagged), and one user per rule combination
(amount only, velocity only, geo only, velocity+amount, geo+amount) plus **`TX-DEMO-FRAUD`** (user `U999`):
Chennai history → burst of Chennai purchases → ₹95,000 in London 10 minutes later = all three rules, score 100.

## Tests
```bash
cd backend
pip install -r requirements.txt
pytest -v
```
Uses an in-memory SQLite database; no PostgreSQL or AWS needed.

## Demo flow (judges)
1. `docker compose up --build` → open http://localhost:5173.
2. Dashboard → **Seed Demo Data** → counters populate.
3. **Flagged Transactions** → `TX-DEMO-FRAUD` is on top (100/100, HIGH). Try search/filters/sorting.
4. Open it: three triggered rules with +30/+35/+40 and reasons; notification status shows the attempted alert.
5. Add a comment → **Mark as Reviewed** → confirm → status REVIEWED, audit trail row appears.
6. Open another flagged transaction → **Clear Transaction**; flags remain, audit shows PENDING → CLEARED.
7. Show `/docs`, then the extensibility demo above (`DeviceMismatchRule`, engine untouched).

## Known limitations
- No authentication (reviewer name is a free-text field); no roles.
- Tables are created with `create_all` (no Alembic migrations).
- Notifications are sent synchronously (short timeouts) rather than through a queue; no retry/dedup.
- Velocity/amount/geo consider only the same user's history (last 90 days, max 1000 rows); no cross-user or device-graph signals.
- Merchant/location are free text; coordinates are client-supplied (no geocoding/IP lookup).
- The frontend Docker image runs the Vite dev server (fine for a demo, not for production).
