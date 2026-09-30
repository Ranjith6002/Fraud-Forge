from datetime import datetime, timedelta, timezone

from app.domain import TransactionContext, TransactionData

BASE = datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)

CITIES = {
    "Chennai": (13.0827, 80.2707),
    "London": (51.5074, -0.1278),
    "Bengaluru": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
}


def at(minutes: float = 0) -> datetime:
    return BASE + timedelta(minutes=minutes)


def tx(tx_id="T", user="U1", amount=1000.0, minutes=0.0, city=None, device=None, timestamp="auto", **kw):
    lat, lon = CITIES[city] if city and city in CITIES else (kw.pop("latitude", None), kw.pop("longitude", None))
    ts = at(minutes) if timestamp == "auto" else timestamp
    loc = city if city is not None else kw.pop("location", None)
    return TransactionData(
        transaction_id=tx_id, user_id=user, amount=amount, currency="INR", latitude=lat, longitude=lon,
        location=loc, timestamp=ts, device_id=device, **kw,
    )


def ctx(*history: TransactionData, user="U1") -> TransactionContext:
    return TransactionContext(user_id=user, history=list(history))


def api_payload(tx_id, user="U1", amount=1000, minutes=0, city=None, **extra):
    loc = city if city is not None else extra.get("location", "Chennai")
    body = {
        "transaction_id": tx_id,
        "user_id": user,
        "amount": amount,
        "timestamp": at(minutes).isoformat(),
        "location": loc,
        **extra,
    }
    if city and city in CITIES:
        body.setdefault("latitude", CITIES[city][0])
        body.setdefault("longitude", CITIES[city][1])
    elif city is None and "latitude" not in extra and "longitude" not in extra:
        body.setdefault("latitude", CITIES["Chennai"][0])
        body.setdefault("longitude", CITIES["Chennai"][1])
    return body
