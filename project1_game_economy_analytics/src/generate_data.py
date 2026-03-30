"""
generate_data.py

Produces realistic synthetic CSVs for the game economy analytics project:
  - data/raw/users.csv
  - data/raw/sessions.csv
  - data/raw/items.csv
  - data/raw/economy_events.csv

Run from the project root:
  python src/generate_data.py
"""

import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
NUM_USERS = 2000
SIM_START = datetime(2024, 1, 1)
SIM_END = datetime(2024, 3, 31)
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"

# Retention curves: probability a user returns on day N after install
D1_RETENTION = 0.40
D7_RETENTION = 0.20
D30_RETENTION = 0.08

# Monetisation rates
IAP_CONVERSION_RATE = 0.05   # fraction of users who ever make an IAP
SOFT_SPEND_RATE = 0.60       # fraction of active users who spend soft currency on a given session

# Items catalogue
ITEMS = [
    # (item_id, item_name, item_type, soft_cost, hard_cost, is_iap)
    ("item_001", "Speed Boost",        "consumable",  50,    0,  False),
    ("item_002", "Shield Pack",        "consumable",  75,    0,  False),
    ("item_003", "XP Booster",         "consumable", 100,    0,  False),
    ("item_004", "Rare Skin",          "cosmetic",   500,    0,  False),
    ("item_005", "Epic Skin",          "cosmetic",     0,   10,  False),
    ("item_006", "Legendary Skin",     "cosmetic",     0,   25,  False),
    ("item_007", "Starter Pack",       "iap",          0,    0,  True),
    ("item_008", "Value Pack",         "iap",          0,    0,  True),
    ("item_009", "Mega Pack",          "iap",          0,    0,  True),
    ("item_010", "Season Pass",        "iap",          0,    0,  True),
]

# IAP prices in USD
IAP_PRICES = {
    "item_007": 0.99,
    "item_008": 4.99,
    "item_009": 9.99,
    "item_010": 14.99,
}

COUNTRIES = ["US", "GB", "DE", "FR", "CA", "BR", "JP", "KR", "AU", "MX"]
COUNTRY_WEIGHTS = [30, 10, 8, 7, 6, 8, 6, 5, 4, 5]  # rough relative traffic

PLATFORMS = ["iOS", "Android"]
PLATFORM_WEIGHTS = [45, 55]

CHANNELS = ["organic", "paid_social", "paid_search", "influencer", "email"]
CHANNEL_WEIGHTS = [40, 25, 15, 12, 8]

DEVICE_TYPES = ["phone", "tablet"]
DEVICE_WEIGHTS = [85, 15]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def random_ts(date: datetime, hour_start=6, hour_end=23) -> datetime:
    """Random timestamp within waking hours on a given date."""
    hour = random.randint(hour_start, hour_end)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return date.replace(hour=hour, minute=minute, second=second)


def date_range(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def sim_days():
    return (SIM_END - SIM_START).days + 1


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_users():
    users = []
    sim_days_total = (SIM_END - SIM_START).days

    for i in range(NUM_USERS):
        install_offset = random.randint(0, sim_days_total - 30)  # leave room for D30 retention
        install_date = SIM_START + timedelta(days=install_offset)
        users.append({
            "user_id": f"u_{i+1:05d}",
            "install_date": install_date.strftime("%Y-%m-%d"),
            "country": weighted_choice(COUNTRIES, COUNTRY_WEIGHTS),
            "platform": weighted_choice(PLATFORMS, PLATFORM_WEIGHTS),
            "acquisition_channel": weighted_choice(CHANNELS, CHANNEL_WEIGHTS),
            "device_type": weighted_choice(DEVICE_TYPES, DEVICE_WEIGHTS),
            "_install_dt": install_date,  # internal, stripped before writing
        })
    return users


def generate_active_dates(user: dict) -> list[datetime]:
    """
    Decide which days a user is active, based on realistic retention curves.
    Always active on install day. Probabilistically active on subsequent days.
    """
    install_dt = user["_install_dt"]
    active = set()
    active.add(install_dt)

    max_day = (SIM_END - install_dt).days

    for delta in range(1, max_day + 1):
        # Retention probability decays with day number
        if delta == 1:
            p = D1_RETENTION
        elif delta <= 7:
            p = D1_RETENTION * (D7_RETENTION / D1_RETENTION) ** ((delta - 1) / 6)
        elif delta <= 30:
            p = D7_RETENTION * (D30_RETENTION / D7_RETENTION) ** ((delta - 7) / 23)
        else:
            p = D30_RETENTION * 0.5 ** ((delta - 30) / 30)

        if random.random() < p:
            active.add(install_dt + timedelta(days=delta))

    return sorted(active)


def generate_sessions(users: list[dict]) -> list[dict]:
    sessions = []
    for user in users:
        active_dates = generate_active_dates(user)
        session_number = 0
        for day in active_dates:
            # 1-3 sessions per active day
            num_sessions = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            day_sessions = sorted(random.randint(6 * 60, 22 * 60) for _ in range(num_sessions))
            for start_mins in day_sessions:
                session_number += 1
                start_ts = day + timedelta(minutes=start_mins)
                duration_mins = random.choices(
                    [2, 5, 10, 20, 40, 60],
                    weights=[10, 25, 30, 20, 10, 5]
                )[0]
                end_ts = start_ts + timedelta(minutes=duration_mins)
                sessions.append({
                    "session_id": f"s_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"],
                    "session_start_ts": start_ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "session_end_ts": end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "session_number": session_number,
                    "_start_dt": start_ts,  # internal
                })
    return sessions


def generate_items() -> list[dict]:
    return [
        {
            "item_id": item[0],
            "item_name": item[1],
            "item_type": item[2],
            "soft_cost": item[3],
            "hard_cost": item[4],
            "is_iap": item[5],
        }
        for item in ITEMS
    ]


def generate_economy_events(users: list[dict], sessions: list[dict]) -> list[dict]:
    # Decide which users are payers
    payer_ids = set(
        u["user_id"]
        for u in random.sample(users, k=int(len(users) * IAP_CONVERSION_RATE))
    )

    soft_items = [i for i in ITEMS if not i[5] and i[3] > 0]   # have soft_cost
    iap_items = [i for i in ITEMS if i[5]]

    events = []

    for session in sessions:
        user_id = session["user_id"]
        session_id = session["session_id"]
        session_start = session["_start_dt"]

        # Soft currency earn (small random amount, most sessions)
        if random.random() < 0.85:
            earn_ts = session_start + timedelta(seconds=random.randint(30, 120))
            events.append({
                "event_id": f"e_{uuid.uuid4().hex[:12]}",
                "user_id": user_id,
                "session_id": session_id,
                "event_ts": earn_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "earn_soft",
                "item_id": "",
                "soft_delta": random.randint(10, 100),
                "hard_delta": 0,
                "revenue_usd": 0.0,
                "txn_id": "",
            })

        # Soft currency spend
        if random.random() < SOFT_SPEND_RATE:
            item = random.choice(soft_items)
            spend_ts = session_start + timedelta(seconds=random.randint(60, 300))
            events.append({
                "event_id": f"e_{uuid.uuid4().hex[:12]}",
                "user_id": user_id,
                "session_id": session_id,
                "event_ts": spend_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "spend_soft",
                "item_id": item[0],
                "soft_delta": -item[3],
                "hard_delta": 0,
                "revenue_usd": 0.0,
                "txn_id": "",
            })

        # IAP purchase (payers only, low per-session probability to spread over time)
        if user_id in payer_ids and random.random() < 0.04:
            item = random.choice(iap_items)
            iap_ts = session_start + timedelta(seconds=random.randint(120, 600))
            txn_id = f"txn_{uuid.uuid4().hex[:10]}"
            events.append({
                "event_id": f"e_{uuid.uuid4().hex[:12]}",
                "user_id": user_id,
                "session_id": session_id,
                "event_ts": iap_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "iap_purchase",
                "item_id": item[0],
                "soft_delta": 0,
                "hard_delta": 0,
                "revenue_usd": IAP_PRICES[item[0]],
                "txn_id": txn_id,
            })

    return events


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):,} rows → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    random.seed(RANDOM_SEED)
    print("Generating synthetic game economy data...")

    users = generate_users()
    print(f"  {len(users):,} users generated")

    sessions = generate_sessions(users)
    print(f"  {len(sessions):,} sessions generated")

    items = generate_items()
    economy_events = generate_economy_events(users, sessions)
    print(f"  {len(economy_events):,} economy events generated")

    print(f"\nWriting CSVs to {OUTPUT_DIR}/")

    write_csv(
        OUTPUT_DIR / "users.csv",
        users,
        ["user_id", "install_date", "country", "platform", "acquisition_channel", "device_type"],
    )
    write_csv(
        OUTPUT_DIR / "sessions.csv",
        sessions,
        ["session_id", "user_id", "session_start_ts", "session_end_ts", "session_number"],
    )
    write_csv(
        OUTPUT_DIR / "items.csv",
        items,
        ["item_id", "item_name", "item_type", "soft_cost", "hard_cost", "is_iap"],
    )
    write_csv(
        OUTPUT_DIR / "economy_events.csv",
        economy_events,
        ["event_id", "user_id", "session_id", "event_ts", "event_type",
         "item_id", "soft_delta", "hard_delta", "revenue_usd", "txn_id"],
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
