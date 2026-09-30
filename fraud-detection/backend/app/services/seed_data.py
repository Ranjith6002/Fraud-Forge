"""Deterministic demo dataset (pure Python, no DB) used by POST /api/seed."""
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

CITIES = {
    "Chennai": (13.0827, 80.2707),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Delhi": (28.6139, 77.2090),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "London": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Dubai": (25.2048, 55.2708),
}

DEMO_FRAUD_ID = "TX-DEMO-FRAUD"


def build_demo_dataset(now: datetime) -> List[Dict[str, Any]]:
    """Return transaction dicts (oldest first) whose timestamps are all before `now`."""
    rng = random.Random(42)
    rows: List[Dict[str, Any]] = []

    def add(user, city, amount, ts, merchant, device=None, tx_id=None):
        lat, lon = CITIES[city]
        rows.append({
            "transaction_id": tx_id, "user_id": user, "amount": round(float(amount), 2),
            "currency": "INR", "merchant": merchant,
            "latitude": round(lat + rng.uniform(-0.02, 0.02), 5),
            "longitude": round(lon + rng.uniform(-0.02, 0.02), 5),
            "location": city, "timestamp": ts, "device_id": device,
        })

    def history(user, city, amounts, days_ago_start, merchant="Grocery Mart", device=None):
        """One transaction per ~day starting `days_ago_start` days ago."""
        for i, amt in enumerate(amounts):
            ts = now - timedelta(days=days_ago_start - i, hours=rng.randint(0, 5))
            add(user, city, amt, ts, merchant, device)

    # 1) Normal customers: steady spending, same city (no flags expected).
    pattern = [1200, 850, 2400, 1800, 3100, 950, 2200, 1500]
    merchants = ["Grocery Mart", "Fuel Station", "Coffee House", "Metro Recharge", "Pharmacy"]
    for n, (user, city) in enumerate(
        [("U101", "Chennai"), ("U102", "Mumbai"), ("U103", "Bengaluru"),
         ("U104", "Delhi"), ("U105", "Hyderabad"), ("U106", "Pune")]
    ):
        for i, amt in enumerate(pattern):
            ts = now - timedelta(days=13 - i * 1.5, hours=rng.randint(0, 6) - n)
            add(user, city, amt * (0.8 + 0.1 * n), ts, merchants[(i + n) % len(merchants)], f"dev-{user}")

    # 1b) Legitimate travel: Delhi -> Mumbai a day later (must NOT be flagged).
    for i, amt in enumerate([1800, 2100, 1900, 2000]):
        add("U107", "Delhi", amt, now - timedelta(days=9 - i), "Metro Recharge", "dev-U107")
    for i, amt in enumerate([2200, 1700, 2500]):
        add("U107", "Mumbai", amt, now - timedelta(days=4.5 - i), "Cafe Leopold", "dev-U107")

    # 2) UNUSUAL_AMOUNT only.
    history("U200", "Mumbai", [3200, 4100, 3800, 4400, 3600], 7, device="dev-U200")
    add("U200", "Mumbai", 85000, now - timedelta(hours=2), "Luxury Jewellers", "dev-U200")

    # 3) HIGH_VELOCITY only (7 small purchases in 6 minutes).
    history("U300", "Delhi", [1200, 1100, 1300], 5, device="dev-U300")
    base = now - timedelta(minutes=90)
    for m in range(7):
        add("U300", "Delhi", 499, base + timedelta(minutes=m), "QuickMart Online", "dev-U300")

    # 4) IMPOSSIBLE_GEO only (Mumbai -> New York in 25 minutes).
    history("U400", "Mumbai", [1800, 2200, 1500, 2500], 6, device="dev-U400")
    base = now - timedelta(minutes=100)
    add("U400", "Mumbai", 1800, base, "Airport Duty Free", "dev-U400")
    add("U400", "New York", 2200, base + timedelta(minutes=25), "Times Square Store", "dev-U400")

    # 5) HIGH_VELOCITY + UNUSUAL_AMOUNT (MEDIUM).
    history("U500", "Bengaluru", [2500, 2200, 2800, 2400], 6, device="dev-U500")
    base = now - timedelta(minutes=60)
    for m, amt in enumerate([300, 250, 400, 350, 300]):
        add("U500", "Bengaluru", amt, base + timedelta(minutes=m), "Recharge Hub", "dev-U500")
    add("U500", "Bengaluru", 48000, base + timedelta(minutes=5), "Electronics Depot", "dev-U500")

    # 6) IMPOSSIBLE_GEO + UNUSUAL_AMOUNT (HIGH).
    history("U600", "Hyderabad", [3500, 4200, 3900, 4600, 4000], 6, device="dev-U600")
    base = now - timedelta(minutes=110)
    add("U600", "Hyderabad", 3800, base, "Tech Bazaar", "dev-U600")
    add("U600", "Dubai", 52000, base + timedelta(minutes=40), "Gold Souk Trading", "dev-U600")

    # 7) THE PERFECT DEMO FRAUD: all three rules, score capped at 100.
    history("U999", "Chennai", [1800, 2400, 1900, 2100], 4, device="dev-U999")
    base = now - timedelta(minutes=30)
    add("U999", "Chennai", 2000, base, "Chennai Metro Recharge", "dev-U999")
    for m in (2, 4, 6, 8):
        add("U999", "Chennai", 2000, base + timedelta(minutes=m), "Chennai Metro Recharge", "dev-U999")
    add("U999", "London", 95000, base + timedelta(minutes=10), "Harrods Online London",
        "dev-UNKNOWN", tx_id=DEMO_FRAUD_ID)

    rows.sort(key=lambda r: r["timestamp"])
    counter = 1001
    for row in rows:
        if not row["transaction_id"]:
            row["transaction_id"] = f"TX{counter}"
            counter += 1
    return rows
