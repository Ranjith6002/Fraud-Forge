"""Deterministic demo dataset (pure Python, no DB) used by POST /api/seed and seed_demo_data.py."""
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
    "Kolkata": (22.5726, 88.3639),
    "London": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Dubai": (25.2048, 55.2708),
    "Singapore": (1.3521, 103.8198),
}

DEMO_FRAUD_ID = "TX-DEMO-FRAUD"


def build_demo_dataset(now: datetime) -> List[Dict[str, Any]]:
    """Return transaction dicts (oldest first) whose timestamps are all before `now`."""
    rng = random.Random(42)
    rows: List[Dict[str, Any]] = []

    def add(user: str, city: str, amount: float, ts: datetime, merchant: str, device: str = None, tx_id: str = None):
        lat, lon = CITIES[city]
        rows.append({
            "transaction_id": tx_id,
            "user_id": user,
            "amount": round(float(amount), 2),
            "currency": "INR",
            "merchant": merchant,
            "latitude": round(lat + rng.uniform(-0.02, 0.02), 5),
            "longitude": round(lon + rng.uniform(-0.02, 0.02), 5),
            "location": city,
            "timestamp": ts,
            "device_id": device or f"dev-{user}",
        })

    def history(user: str, city: str, amounts: List[float], days_ago_start: float, merchant: str = "Grocery Mart", device: str = None):
        """Historical background transactions for context baseline."""
        for i, amt in enumerate(amounts):
            ts = now - timedelta(days=days_ago_start - (i * 0.8), hours=rng.randint(0, 4))
            add(user, city, amt, ts, merchant, device)

    # -------------------------------------------------------------------------
    # 1) Normal Customers (LOW risk - steady spending, same/plausible locations)
    # -------------------------------------------------------------------------
    pattern = [1200, 850, 2400, 1800, 3100, 950, 2200, 1500]
    merchants = ["Grocery Mart", "Fuel Station", "Coffee House", "Metro Recharge", "Pharmacy", "Supermarket", "Bookstore"]
    normal_users = [
        ("CUST-1001", "Chennai"),
        ("CUST-1002", "Mumbai"),
        ("CUST-1003", "Bengaluru"),
        ("CUST-1004", "Delhi"),
        ("CUST-1005", "Hyderabad"),
        ("CUST-1006", "Pune"),
        ("CUST-1007", "Kolkata"),
    ]
    for n, (user, city) in enumerate(normal_users):
        for i, amt in enumerate(pattern):
            ts = now - timedelta(days=25 - i * 2.8, hours=rng.randint(0, 5) + n)
            m_name = merchants[(i + n) % len(merchants)]
            add(user, city, amt * (0.85 + 0.05 * n), ts, m_name, f"dev-{user}")

    # Legitimate travel: Delhi -> Mumbai 3 days later (plausible travel speed)
    for i, amt in enumerate([1800, 2100, 1900, 2000]):
        add("CUST-1008", "Delhi", amt, now - timedelta(days=12 - i * 2), "Metro Recharge", "dev-CUST-1008")
    for i, amt in enumerate([2200, 1700, 2500]):
        add("CUST-1008", "Mumbai", amt, now - timedelta(days=4 - i), "Cafe Leopold", "dev-CUST-1008")

    # Legitimate travel: Chennai -> Bengaluru 2 days later
    for i, amt in enumerate([1500, 2300, 1950]):
        add("CUST-1009", "Chennai", amt, now - timedelta(days=8 - i), "Apollo Pharmacy", "dev-CUST-1009")
    for i, amt in enumerate([3100, 2800]):
        add("CUST-1009", "Bengaluru", amt, now - timedelta(days=3 - i), "Indiranagar Bistro", "dev-CUST-1009")

    # -------------------------------------------------------------------------
    # 2) UNUSUAL_AMOUNT Fraud Scenarios (HIGH / MEDIUM risk)
    # -------------------------------------------------------------------------
    # Scenario A: CUST-2000 - normal history avg ~₹3,800, then sudden ₹95,000 purchase at Zaveri Jewellers
    history("CUST-2000", "Mumbai", [3200, 4100, 3800, 4400, 3600], 15, device="dev-CUST-2000")
    add("CUST-2000", "Mumbai", 95000, now - timedelta(hours=3), "Zaveri Jewellers Mumbai", "dev-CUST-2000", tx_id="TX-AMT-HIGH-01")

    # Scenario B: CUST-2001 - normal history avg ~₹1,800, then ₹58,000 purchase at Apple Flagship Store
    history("CUST-2001", "Delhi", [1800, 2100, 1600, 1950, 1700], 12, device="dev-CUST-2001")
    add("CUST-2001", "Delhi", 58000, now - timedelta(hours=6), "Apple Flagship Store Delhi", "dev-CUST-2001", tx_id="TX-AMT-MED-02")

    # -------------------------------------------------------------------------
    # 3) HIGH_VELOCITY Fraud Scenarios (HIGH / MEDIUM risk)
    # -------------------------------------------------------------------------
    # Scenario A: CUST-3000 - 7 rapid transactions in 6 minutes (card testing burst)
    history("CUST-3000", "Delhi", [1200, 1100, 1300], 10, device="dev-CUST-3000")
    base_vel1 = now - timedelta(minutes=140)
    for m in range(7):
        add("CUST-3000", "Delhi", 499 + m * 50, base_vel1 + timedelta(minutes=m * 0.8), "QuickMart Online", "dev-CUST-3000")

    # Scenario B: CUST-3001 - 6 rapid transactions in 5 minutes
    history("CUST-3001", "Chennai", [1500, 1400, 1600], 8, device="dev-CUST-3001")
    base_vel2 = now - timedelta(minutes=180)
    for m in range(6):
        add("CUST-3001", "Chennai", 299 + m * 20, base_vel2 + timedelta(minutes=m * 0.7), "Gaming Credits TopUp", "dev-CUST-3001")

    # -------------------------------------------------------------------------
    # 4) IMPOSSIBLE_GEO Fraud Scenarios (HIGH risk - impossible physical travel speed)
    # -------------------------------------------------------------------------
    # Scenario A: CUST-4000 - Mumbai -> New York in 20 minutes (over 12,500 km/h required)
    history("CUST-4000", "Mumbai", [1800, 2200, 1500, 2500], 9, device="dev-CUST-4000")
    base_geo1 = now - timedelta(minutes=110)
    add("CUST-4000", "Mumbai", 1800, base_geo1, "Mumbai Airport Duty Free", "dev-CUST-4000")
    add("CUST-4000", "New York", 2400, base_geo1 + timedelta(minutes=20), "Times Square Electronics NY", "dev-CUST-4000", tx_id="TX-GEO-HIGH-01")

    # Scenario B: CUST-4001 - Chennai -> London in 15 minutes
    history("CUST-4001", "Chennai", [2100, 1900, 2400], 7, device="dev-CUST-4001")
    base_geo2 = now - timedelta(minutes=150)
    add("CUST-4001", "Chennai", 2100, base_geo2, "Chennai Metro Counter", "dev-CUST-4001")
    add("CUST-4001", "London", 3500, base_geo2 + timedelta(minutes=15), "Harrods Store London", "dev-CUST-4001", tx_id="TX-GEO-HIGH-02")

    # -------------------------------------------------------------------------
    # 5) MULTI-RULE FRAUD Scenarios (HIGH risk)
    # -------------------------------------------------------------------------
    # Scenario A: CUST-5000 - Velocity + Unusual Amount
    history("CUST-5000", "Bengaluru", [2500, 2200, 2800, 2400], 8, device="dev-CUST-5000")
    base_m1 = now - timedelta(minutes=75)
    for m, amt in enumerate([300, 250, 400, 350, 300]):
        add("CUST-5000", "Bengaluru", amt, base_m1 + timedelta(minutes=m), "Recharge Hub", "dev-CUST-5000")
    add("CUST-5000", "Bengaluru", 62000, base_m1 + timedelta(minutes=6), "Croma Mega Electronics", "dev-CUST-5000", tx_id="TX-MULTI-MED-01")

    # Scenario B: CUST-6000 - Impossible Geo + Unusual Amount
    history("CUST-6000", "Hyderabad", [3500, 4200, 3900, 4600, 4000], 10, device="dev-CUST-6000")
    base_m2 = now - timedelta(minutes=95)
    add("CUST-6000", "Hyderabad", 3800, base_m2, "Cyberabad Tech Park", "dev-CUST-6000")
    add("CUST-6000", "Dubai", 78000, base_m2 + timedelta(minutes=35), "Gold Souk Trading Dubai", "dev-CUST-6000", tx_id="TX-MULTI-HIGH-01")

    # -------------------------------------------------------------------------
    # 6) THE PERFECT DEMO FRAUD: Triggers ALL 3 rules (Velocity + Amount + Geo)
    # Risk Score: 30 + 35 + 40 = 105 -> Clamped to 100 (HIGH Risk)
    # -------------------------------------------------------------------------
    history("CUST-9999", "Chennai", [1800, 2400, 1900, 2100], 6, device="dev-CUST-9999")
    base_perfect = now - timedelta(minutes=25)
    add("CUST-9999", "Chennai", 2000, base_perfect, "Chennai Central Railway", "dev-CUST-9999")
    for m in (2, 4, 6, 8):
        add("CUST-9999", "Chennai", 2000, base_perfect + timedelta(minutes=m), "Chennai Central Railway", "dev-CUST-9999")
    # 10 minutes later in London with ₹1,25,000 purchase from unknown device
    add(
        "CUST-9999",
        "London",
        125000,
        base_perfect + timedelta(minutes=10),
        "Harrods Online Luxury London",
        "dev-UNKNOWN-99",
        tx_id=DEMO_FRAUD_ID,
    )

    # Sort dataset chronologically
    rows.sort(key=lambda r: r["timestamp"])

    # Assign clean deterministic transaction IDs if not explicitly provided
    counter = 1001
    for row in rows:
        if not row["transaction_id"]:
            row["transaction_id"] = f"TX-{counter}"
            counter += 1


    return rows

