"""Health + metadata routes."""
from flask import jsonify

from sahaay import config
from sahaay.dates import utc_now_iso, week_strip
from sahaay.storage import get_store
from sahaay.validation import CATEGORIES, FREQUENCIES, WORK_TYPES
from sahaay.routes import api_bp


@api_bp.get("/health")
def health():
    store = get_store()
    info = {
        "status": "ok",
        "store": store.kind,
        "store_detail": store.describe(),
        "sheets_configured": config.sheets_configured(),
        "time": utc_now_iso(),
    }
    if hasattr(store, "service_account_email"):
        info["service_account"] = store.service_account_email
    return jsonify(info)


@api_bp.get("/meta")
def meta():
    store = get_store()
    week = week_strip(7)
    return jsonify({
        "categories": [
            {"id": "maid", "label": "Maid"},
            {"id": "electrician", "label": "Electrician"},
            {"id": "carpenter", "label": "Carpenter"},
            {"id": "other", "label": "Other Local Service"},
        ],
        "work_types": [{"id": w, "label": {"cleaning": "House cleaning", "cooking": "Cooking",
                                           "both": "Cleaning & Cooking"}[w]} for w in WORK_TYPES],
        "frequencies": [
            {"id": "one_time", "label": "One-time service"},
            {"id": "daily", "label": "Daily recurring"},
            {"id": "weekly", "label": "Weekly recurring"},
        ],
        "bookings_auto_accept": True,
        "today": week[0]["date"],
        "week": week,
        "store": store.kind,
    })
