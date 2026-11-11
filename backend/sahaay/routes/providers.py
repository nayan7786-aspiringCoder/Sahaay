"""Provider routes — registration, search/filter, profiles, availability, timetable."""
import uuid

from flask import jsonify, request

from sahaay.dates import today_iso, utc_now_iso, weekday_of
from sahaay.errors import ApiError
from sahaay.storage import get_store
from sahaay.timetable import build_timetable
from sahaay.validation import (
    CATEGORIES,
    as_bool,
    clean_enum,
    validate_availability_patch,
    validate_provider_payload,
)
from sahaay.routes import api_bp


def mask_phone(phone: str | None) -> str:
    """+919826011223 → +91 98XXX XXX23 — contact details stay private for maids."""
    if not phone:
        return ""
    digits = phone.replace("+91", "")
    return f"+91 {digits[:2]}XXX XXX{digits[-2:]}"


def provider_public(provider: dict, reveal_phone: bool = False) -> dict:
    """Public-safe profile: no sensitive fields exist by design (never Aadhaar)."""
    out = {
        "id": provider["id"],
        "name": provider["name"],
        "category": provider["category"],
        "specialty": provider.get("specialty"),
        "work_type": provider.get("work_type"),
        "shop_address": provider.get("shop_address"),
        "morning_available": bool(provider.get("morning_available")),
        "morning_start": provider.get("morning_start"),
        "morning_end": provider.get("morning_end"),
        "evening_available": bool(provider.get("evening_available")),
        "evening_start": provider.get("evening_start"),
        "evening_end": provider.get("evening_end"),
        "wants_regular": bool(provider.get("wants_regular")),
        "verified": bool(provider.get("verified")),
        "created_at": provider.get("created_at"),
    }
    if out["category"] == "maid":
        out["phone_masked"] = mask_phone(provider.get("phone"))
        if reveal_phone:
            out["phone"] = provider.get("phone")
    else:
        out["phone"] = provider.get("phone")
    return out


@api_bp.post("/providers")
def register_provider():
    store = get_store()
    cleaned = validate_provider_payload(request.get_json(silent=True) or {})
    provider = {
        **cleaned,
        "id": str(uuid.uuid4()),
        # Safe verification placeholder — identity documents (e.g. Aadhaar) are
        # deliberately never collected or stored.
        "verified": False,
        "created_at": utc_now_iso(),
    }
    store.insert_provider(provider)
    return jsonify(provider_public(provider)), 201


@api_bp.get("/providers")
def search_providers():
    store = get_store()
    args = request.args

    category = args.get("category")
    if category and category not in CATEGORIES:
        raise ApiError(400, "VALIDATION_ERROR", f"Unknown category “{category}”.",
                       [{"field": "category", "allowed": list(CATEGORIES)}])
    shift = args.get("shift")
    if shift and shift not in ("morning", "evening"):
        raise ApiError(400, "VALIDATION_ERROR", "shift must be morning or evening.",
                       [{"field": "shift"}])
    work_type = args.get("work_type") or None
    regular = as_bool(args["regular"], "regular") if "regular" in args else None
    query = (args.get("q") or "").strip().lower()

    providers = store.list_providers()
    out = []
    for p in providers:
        if category and p["category"] != category:
            continue
        if work_type and p["category"] == "maid" and p.get("work_type") != work_type:
            continue
        if shift and not p.get(f"{shift}_available"):
            continue
        if regular is not None and bool(p.get("wants_regular")) is not regular:
            continue
        if query and query not in f"{p['name']} {p.get('specialty') or ''}".lower():
            continue
        out.append(provider_public(p))

    out.sort(key=lambda p: p["name"].lower())
    return jsonify({"providers": out, "count": len(out)})


@api_bp.get("/providers/<provider_id>")
def get_provider(provider_id: str):
    store = get_store()
    provider = store.get_provider(provider_id)
    if not provider:
        raise ApiError(404, "PROVIDER_NOT_FOUND", "No provider found with that id.")
    return jsonify(provider_public(provider))


@api_bp.patch("/providers/<provider_id>")
def update_provider(provider_id: str):
    store = get_store()
    patch = validate_availability_patch(request.get_json(silent=True) or {})
    provider = store.update_provider(provider_id, patch)
    if not provider:
        raise ApiError(404, "PROVIDER_NOT_FOUND", "No provider found with that id.")
    return jsonify(provider_public(provider))


@api_bp.get("/providers/<provider_id>/timetable")
def provider_timetable(provider_id: str):
    store = get_store()
    provider = store.get_provider(provider_id)
    if not provider:
        raise ApiError(404, "PROVIDER_NOT_FOUND", "No provider found with that id.")

    date_str = request.args.get("date") or today_iso()
    # Raises a clean 400 on malformed dates.
    weekday = weekday_of(date_str)

    bookings = store.list_bookings(provider_id)
    timetable = build_timetable(provider_public(provider), bookings, date_str, weekday)
    return jsonify(timetable)
