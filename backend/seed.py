"""Seed Sahaay with realistic demo data (maids, tradespeople, bookings).

Runs against the ACTIVE store — Google Sheets when configured and reachable,
otherwise the local SQLite fallback (offline mode).

Usage:
    cd backend && python seed.py            # idempotent: skips if providers exist
    cd backend && python seed.py --force    # wipe + reseed
"""
import sys
from uuid import uuid4

from sahaay.dates import today_iso, utc_now_iso, weekday_of
from sahaay.storage import get_store

MAIDS = [
    {
        "name": "Sunita Devi", "phone": "+919826011223", "category": "maid",
        "work_type": "cleaning", "specialty": "House cleaning",
        "morning_available": True, "morning_start": "07:00", "morning_end": "11:00",
        "evening_available": False, "evening_start": None, "evening_end": None,
        "wants_regular": True, "verified": True,
    },
    {
        "name": "Kamla Sharma", "phone": "+919826044556", "category": "maid",
        "work_type": "cooking", "specialty": "Cooking",
        "morning_available": True, "morning_start": "08:00", "morning_end": "11:00",
        "evening_available": True, "evening_start": "16:00", "evening_end": "19:00",
        "wants_regular": True, "verified": True,
    },
    {
        "name": "Anita Kumari", "phone": "+919826077889", "category": "maid",
        "work_type": "both", "specialty": "Cleaning & Cooking",
        "morning_available": True, "morning_start": "06:00", "morning_end": "10:00",
        "evening_available": False, "evening_start": None, "evening_end": None,
        "wants_regular": True, "verified": False,
    },
    {
        "name": "Meena Vishwakarma", "phone": "+919826033221", "category": "maid",
        "work_type": "cleaning", "specialty": "House cleaning",
        "morning_available": False, "morning_start": None, "morning_end": None,
        "evening_available": True, "evening_start": "17:00", "evening_end": "21:00",
        "wants_regular": False, "verified": True,
    },
]

TRADES = [
    {
        "name": "Vijay Electric Works", "phone": "+919425066778", "category": "electrician",
        "specialty": "House wiring, inverter & MCB repair",
        "shop_address": "5, Bhawarkuan Main Road, Indore",
        "verified": True,
    },
    {
        "name": "Sharma Electricals", "phone": "+919425022334", "category": "electrician",
        "specialty": "Fan, geyser & appliance repair",
        "shop_address": "Shop 12, Vijay Nagar Market, Indore",
        "verified": True,
    },
    {
        "name": "Rajesh Furniture Works", "phone": "+919425055446", "category": "carpenter",
        "specialty": "Modular kitchens & wardrobe repair",
        "shop_address": "Khandwa Naka, Near Chipa Tank, Indore",
        "verified": False,
    },
    {
        "name": "Ganesh Plumbing & Repair", "phone": "+919425099887", "category": "other",
        "specialty": "Plumber — taps, tanks & bathroom fitting",
        "shop_address": "Sukhlia Market, Indore",
        "verified": False,
    },
]


def main(force: bool) -> None:
    store = get_store()
    print(f"Seeding store: {store.describe()}")

    existing = store.list_providers()
    if existing and not force:
        print(f"Already seeded ({len(existing)} providers). Use --force to wipe and reseed.")
        return
    if force:
        store.clear_all()
        print("Cleared existing data.")

    today = today_iso()
    weekday = weekday_of(today)
    now = utc_now_iso()

    ids: dict[str, str] = {}
    for spec in MAIDS + TRADES:
        provider = {
            **spec,
            "id": str(uuid4()),
            "created_at": now,
        }
        store.insert_provider(provider)
        ids[spec["name"]] = provider["id"]
        print(f"  + {spec['category']:<11} {spec['name']}")

    bookings = [
        {  # one-time booking today → Sunita 07:00 shows red
            "provider": "Sunita Devi", "consumer_name": "Rohit Verma",
            "consumer_phone": "+919039010101", "date": today, "period": "morning",
            "slot_start": "07:00", "slot_end": "08:00", "frequency": "one_time",
        },
        {  # weekly recurring → Kamla 17:00 shows red every week on this weekday
            "provider": "Kamla Sharma", "consumer_name": "Priya Nair",
            "consumer_phone": "+919039020202", "date": today, "period": "evening",
            "slot_start": "17:00", "slot_end": "18:00", "frequency": "weekly",
        },
        {  # daily recurring → Anita 06:00 shows red every day
            "provider": "Anita Kumari", "consumer_name": "Amit Joshi",
            "consumer_phone": "+919039030303", "date": today, "period": "morning",
            "slot_start": "06:00", "slot_end": "07:00", "frequency": "daily",
        },
    ]
    for spec in bookings:
        booking = {
            **spec,
            "id": str(uuid4()),
            "provider_id": ids[spec.pop("provider")],
            "weekday": weekday,
            "status": "accepted",
            "created_at": now,
        }
        store.insert_booking(booking)
        print(f"  + booking     {spec['slot_start']} {spec['frequency']}"
              f" ({spec['consumer_name']})")

    print("Seed complete:")
    for name, provider_id in ids.items():
        print(f"  {provider_id}  {name}")


if __name__ == "__main__":
    main("--force" in sys.argv)
