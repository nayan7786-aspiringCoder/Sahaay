"""Booking routes — creation (auto-accept), accept/reject, updates, conflict checks."""
import uuid

from flask import jsonify, request

from sahaay.dates import today_iso, utc_now_iso, weekday_of
from sahaay.errors import ApiError
from sahaay.storage import get_store
from sahaay.timetable import (
    add_hour,
    booking_blocks,
    slot_period,
    window_covers,
)
from sahaay.validation import (
    FREQUENCIES,
    clean_enum,
    clean_time,
    validate_booking_payload,
)
from sahaay.routes import api_bp
from sahaay.routes.providers import provider_public


def booking_public(booking: dict, store) -> dict:
    provider = store.get_provider(booking["provider_id"])
    return {
        "id": booking["id"],
        "provider_id": booking["provider_id"],
        "provider_name": provider["name"] if provider else None,
        "provider_phone": provider.get("phone") if provider else None,
        "provider_specialty": provider.get("specialty") if provider else None,
        "consumer_name": booking["consumer_name"],
        "consumer_phone": booking["consumer_phone"],
        "date": booking["date"],
        "weekday": int(booking.get("weekday") or 0),
        "period": booking["period"],
        "slot_start": booking["slot_start"],
        "slot_end": booking["slot_end"],
        "frequency": booking["frequency"],
        "status": booking["status"],
        "created_at": booking.get("created_at"),
    }


def _check_conflict(store, provider_id: str, date_str: str, weekday: int,
                    slot_start: str, slot_end: str, exclude_booking_id: str | None = None):
    """409 as soon as an accepted booking already blocks this slot."""
    for existing in store.list_bookings(provider_id):
        if exclude_booking_id and existing["id"] == exclude_booking_id:
            continue
        if booking_blocks(existing, date_str, weekday, slot_start, slot_end):
            raise ApiError(
                409, "SLOT_ALREADY_BOOKED",
                f"{existing['slot_start']}–{existing['slot_end']} is already booked for "
                f"{date_str} ({existing['frequency']}). Please pick another green slot.",
                [{"slot_start": existing["slot_start"], "slot_end": existing["slot_end"],
                  "date": existing["date"], "frequency": existing["frequency"]}],
            )


@api_bp.post("/bookings")
def create_booking():
    store = get_store()
    cleaned = validate_booking_payload(request.get_json(silent=True) or {})

    provider = store.get_provider(cleaned["provider_id"])
    if not provider:
        raise ApiError(404, "PROVIDER_NOT_FOUND", "No provider found with that id.")
    if provider["category"] != "maid":
        raise ApiError(400, "NOT_BOOKABLE",
                       "Timetable booking is for maids — contact tradespeople directly "
                       "on their listed phone number.")

    slot_start = cleaned["slot_start"]
    slot_end = add_hour(slot_start)
    period = slot_period(slot_start)
    date_str = cleaned["date"]
    weekday = weekday_of(date_str)

    if not window_covers(provider, period, slot_start, slot_end):
        raise ApiError(400, "SLOT_NOT_OFFERED",
                       f"{slot_start}–{slot_end} is outside {provider['name']}'s "
                       f"{period} availability ({provider[f'{period}_start']}–"
                       f"{provider[f'{period}_end']}).")

    _check_conflict(store, provider["id"], date_str, weekday, slot_start, slot_end)

    booking = {
        **cleaned,
        "id": str(uuid.uuid4()),
        "period": period,
        "slot_end": slot_end,
        "weekday": weekday,
        # Auto-accept flow (product decision): the request is confirmed instantly.
        "status": "accepted",
        "created_at": utc_now_iso(),
    }
    store.insert_booking(booking)
    return jsonify(booking_public(booking, store)), 201


@api_bp.get("/bookings")
def list_bookings():
    store = get_store()
    provider_id = request.args.get("provider_id")
    if request.args.get("provider_id") and not store.get_provider(provider_id):
        raise ApiError(404, "PROVIDER_NOT_FOUND", "No provider found with that id.")
    bookings = store.list_bookings(provider_id)
    return jsonify({"bookings": [booking_public(b, store) for b in bookings],
                    "count": len(bookings)})


def _get_booking_or_404(store, booking_id: str) -> dict:
    booking = store.get_booking(booking_id)
    if not booking:
        raise ApiError(404, "BOOKING_NOT_FOUND", "No booking found with that id.")
    return booking


@api_bp.get("/bookings/<booking_id>")
def get_booking(booking_id: str):
    store = get_store()
    booking = _get_booking_or_404(store, booking_id)
    return jsonify(booking_public(booking, store))


@api_bp.post("/bookings/<booking_id>/accept")
def accept_booking(booking_id: str):
    store = get_store()
    booking = _get_booking_or_404(store, booking_id)
    if booking["status"] == "accepted":
        return jsonify(booking_public(booking, store))  # idempotent
    if booking["status"] in ("declined", "cancelled"):
        raise ApiError(409, "BOOKING_CLOSED",
                       f"Booking is already {booking['status']} and cannot be accepted.")

    _check_conflict(store, booking["provider_id"], booking["date"],
                    int(booking["weekday"]), booking["slot_start"], booking["slot_end"],
                    exclude_booking_id=booking["id"])
    updated = store.update_booking(booking_id, {"status": "accepted"})
    return jsonify(booking_public(updated, store))


@api_bp.post("/bookings/<booking_id>/reject")
def reject_booking(booking_id: str):
    store = get_store()
    booking = _get_booking_or_404(store, booking_id)
    if booking["status"] in ("declined", "cancelled"):
        return jsonify(booking_public(booking, store))  # idempotent
    updated = store.update_booking(booking_id, {"status": "declined"})
    return jsonify(booking_public(updated, store))


@api_bp.patch("/bookings/<booking_id>")
def update_booking(booking_id: str):
    store = get_store()
    booking = _get_booking_or_404(store, booking_id)
    data = request.get_json(silent=True) or {}

    allowed = {"date", "slot_start", "frequency", "status"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ApiError(400, "VALIDATION_ERROR",
                       f"Unknown field(s): {', '.join(unknown)}. Updatable: "
                       f"{', '.join(sorted(allowed))}.")

    patch = {}
    recheck = False
    if "date" in data:
        from sahaay.validation import clean_date

        patch["date"] = clean_date({"date": data["date"]}, "date")
        recheck = True
    if "slot_start" in data:
        patch["slot_start"] = clean_time(data, "slot_start", label="slot start")
        if patch["slot_start"].split(":")[1] != "00":
            raise ApiError(400, "VALIDATION_ERROR", "Timetable slots start on the hour.")
        patch["slot_end"] = add_hour(patch["slot_start"])
        patch["period"] = slot_period(patch["slot_start"])
        recheck = True
    if "frequency" in data:
        patch["frequency"] = clean_enum(data, "frequency", FREQUENCIES, label="frequency")
        recheck = True
    if "status" in data:
        status = str(data["status"]).strip().lower()
        if status not in ("accepted", "declined", "cancelled"):
            raise ApiError(400, "VALIDATION_ERROR",
                           "status must be accepted, declined or cancelled.")
        patch["status"] = status

    if not patch:
        raise ApiError(400, "VALIDATION_ERROR", "Nothing to update.")

    if recheck and patch.get("status", booking["status"]) == "accepted":
        merged = {**booking, **patch}
        provider = store.get_provider(booking["provider_id"])
        if provider and not window_covers(provider, merged["period"],
                                          merged["slot_start"], merged["slot_end"]):
            raise ApiError(400, "SLOT_NOT_OFFERED",
                           "The new time is outside the provider's availability.")
        _check_conflict(store, booking["provider_id"], merged["date"],
                        weekday_of(merged["date"]), merged["slot_start"],
                        merged["slot_end"], exclude_booking_id=booking["id"])

    updated = store.update_booking(booking_id, patch)
    return jsonify(booking_public(updated, store))
