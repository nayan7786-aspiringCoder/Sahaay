"""Input validation and cleaning.

Flask does not validate bodies for us, so every route cleans its payload here and
raises ApiError(400, "VALIDATION_ERROR", ...) with field-level details.
"""
import re

from sahaay.errors import ApiError

CATEGORIES = ("maid", "electrician", "carpenter", "other")
WORK_TYPES = ("cleaning", "cooking", "both")
FREQUENCIES = ("one_time", "daily", "weekly")
PERIODS = ("morning", "evening")

PHONE_RE = re.compile(r"^(\+91[\-\s]?)?([6-9]\d{9})$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
DATE_FMT = "%Y-%m-%d"

# Hour grid: 06:00 ... 21:00 (same bounds the timetable renders)
GRID_START_HOUR = 6
GRID_END_HOUR = 21
MORNING_END = "12:00"  # slots starting before 12:00 are "morning"


def validation_error(message: str, details: list | None = None) -> ApiError:
    return ApiError(400, "VALIDATION_ERROR", message, details)


def get_body() -> dict:
    from flask import request

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise validation_error("Request body must be a JSON object.")
    return data


def clean_str(data: dict, field: str, *, required: bool = True, min_len: int = 1,
              max_len: int = 200, label: str | None = None) -> str | None:
    label = label or field.replace("_", " ")
    value = data.get(field)
    if value is None or str(value).strip() == "":
        if required:
            raise validation_error(f"{label.capitalize()} is required.", [{"field": field}])
        return None
    value = " ".join(str(value).split())
    if len(value) < min_len:
        raise validation_error(f"{label.capitalize()} must be at least {min_len} characters.",
                               [{"field": field}])
    if len(value) > max_len:
        raise validation_error(f"{label.capitalize()} must be at most {max_len} characters.",
                               [{"field": field}])
    return value


def clean_phone(data: dict, field: str, *, required: bool = True,
                label: str | None = None) -> str | None:
    """Indian mobile: 10 digits, optional +91 prefix. Stored as +91XXXXXXXXXX."""
    label = label or "phone number"
    raw = data.get(field)
    if raw is None or str(raw).strip() == "":
        if required:
            raise validation_error(f"{label.capitalize()} is required.", [{"field": field}])
        return None
    match = PHONE_RE.match(str(raw).strip())
    if not match:
        raise validation_error("Enter a valid Indian mobile number (10 digits, optional +91).",
                               [{"field": field}])
    return f"+91{match.group(2)}"


def clean_time(data: dict, field: str, *, required: bool = True,
               label: str | None = None) -> str | None:
    label = label or "time"
    value = data.get(field)
    if value is None or str(value).strip() == "":
        if required:
            raise validation_error(f"{label.capitalize()} is required (HH:MM).", [{"field": field}])
        return None
    value = str(value).strip()
    if not TIME_RE.match(value):
        raise validation_error(f"Invalid time “{value}” — use 24-hour HH:MM.", [{"field": field}])
    return value


def clean_date(data: dict, field: str, *, required: bool = True) -> str | None:
    from datetime import datetime

    value = data.get(field)
    if value is None or str(value).strip() == "":
        if required:
            raise validation_error("Date is required (YYYY-MM-DD).", [{"field": field}])
        return None
    value = str(value).strip()
    try:
        datetime.strptime(value, DATE_FMT)
    except ValueError:
        raise validation_error(f"Invalid date “{value}” — use YYYY-MM-DD.", [{"field": field}]) from None
    return value


def clean_enum(data: dict, field: str, allowed: tuple, *, required: bool = True,
               label: str | None = None) -> str | None:
    label = label or field.replace("_", " ")
    value = data.get(field)
    if value is None or str(value).strip() == "":
        if required:
            raise validation_error(f"{label.capitalize()} is required ({' / '.join(allowed)}).",
                                   [{"field": field, "allowed": list(allowed)}])
        return None
    value = str(value).strip().lower()
    if value not in allowed:
        raise validation_error(f"{label.capitalize()} must be one of: {', '.join(allowed)}.",
                               [{"field": field, "allowed": list(allowed)}])
    return value


def as_bool(value, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ("true", "false", "1", "0", "yes", "no"):
        return value.lower() in ("true", "1", "yes")
    raise validation_error(f"{field.replace('_', ' ').capitalize()} must be true or false.",
                           [{"field": field}])


def _apply_shift(out: dict, data: dict, period: str) -> None:
    """Validate one availability window (morning/evening) from the payload."""
    available = as_bool(data.get(f"{period}_available", False), f"{period}_available")
    out[f"{period}_available"] = available
    if not available:
        out[f"{period}_start"] = None
        out[f"{period}_end"] = None
        return

    start = clean_time(data, f"{period}_start", label=f"{period} start time")
    end = clean_time(data, f"{period}_end", label=f"{period} end time")
    bounds = ("06:00", MORNING_END) if period == "morning" else (MORNING_END, "21:00")
    if not (bounds[0] <= start < end <= bounds[1]):
        raise validation_error(
            f"{period.capitalize()} times must run start < end within "
            f"{bounds[0]}–{bounds[1]} (24-hour HH:MM).",
            [{"field": f"{period}_start"}, {"field": f"{period}_end"}],
        )
    out[f"{period}_start"] = start
    out[f"{period}_end"] = end


WORK_TYPE_LABELS = {"cleaning": "House cleaning", "cooking": "Cooking", "both": "Cleaning & Cooking"}


def validate_provider_payload(data: dict) -> dict:
    """Full registration payload → cleaned provider fields (per category)."""
    out: dict = {
        "name": clean_str(data, "name", min_len=2, max_len=80),
        "phone": clean_phone(data, "phone"),
        "category": clean_enum(data, "category", CATEGORIES, label="service category"),
        "work_type": None,
        "specialty": "",
        "shop_address": None,
        "morning_available": False, "morning_start": None, "morning_end": None,
        "evening_available": False, "evening_start": None, "evening_end": None,
        "wants_regular": False,
    }
    category = out["category"]

    if category == "maid":
        out["work_type"] = clean_enum(data, "work_type", WORK_TYPES, label="type of work")
        out["specialty"] = WORK_TYPE_LABELS[out["work_type"]]
        _apply_shift(out, data, "morning")
        _apply_shift(out, data, "evening")
        if not (out["morning_available"] or out["evening_available"]):
            raise validation_error("Set at least one shift — morning or evening availability.",
                                   [{"field": "morning_available"}, {"field": "evening_available"}])
        out["wants_regular"] = as_bool(data.get("wants_regular", False), "wants_regular")
    else:
        out["specialty"] = clean_str(data, "specialty", min_len=3, max_len=120, label="specialty")
        out["shop_address"] = clean_str(data, "shop_address", min_len=5, max_len=200,
                                        label="shop address")

    return out


def validate_availability_patch(data: dict) -> dict:
    """Partial update of provider availability / listing fields."""
    allowed = {"morning_available", "morning_start", "morning_end",
               "evening_available", "evening_start", "evening_end",
               "wants_regular", "specialty", "shop_address"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise validation_error(f"Unknown field(s): {', '.join(unknown)}.", [
            {"field": f} for f in unknown
        ])

    out: dict = {}
    for period in ("morning", "evening"):
        window_changed = any(
            f"{period}_{suffix}" in data for suffix in ("available", "start", "end")
        )
        if window_changed:
            base = {
                f"{period}_available": data.get(f"{period}_available", False),
                f"{period}_start": data.get(f"{period}_start"),
                f"{period}_end": data.get(f"{period}_end"),
            }
            _apply_shift(out, base, period)

    if "wants_regular" in data:
        out["wants_regular"] = as_bool(data["wants_regular"], "wants_regular")
    if "specialty" in data:
        out["specialty"] = clean_str(data, "specialty", min_len=3, max_len=120, label="specialty")
    if "shop_address" in data:
        out["shop_address"] = clean_str(data, "shop_address", min_len=5, max_len=200,
                                        label="shop address")
    if not out:
        raise validation_error("Nothing to update — send at least one availability field.")
    return out


def validate_booking_payload(data: dict) -> dict:
    from sahaay.dates import today_iso

    slot_start = clean_time(data, "slot_start", label="slot start")
    hour, minute = slot_start.split(":")
    if minute != "00":
        raise validation_error("Timetable slots start on the hour (e.g. 07:00).",
                               [{"field": "slot_start"}])
    if not (GRID_START_HOUR <= int(hour) < GRID_END_HOUR):
        raise validation_error(
            f"Slots run between {GRID_START_HOUR:02d}:00 and {GRID_END_HOUR:02d}:00.",
            [{"field": "slot_start"}])

    return {
        "provider_id": clean_str(data, "provider_id", max_len=64),
        "date": clean_date(data, "date", required=False) or today_iso(),
        "slot_start": slot_start,
        "consumer_name": clean_str(data, "consumer_name", min_len=2, max_len=80,
                                   label="your name"),
        "consumer_phone": clean_phone(data, "consumer_phone", label="your phone number"),
        "frequency": clean_enum(data, "frequency", FREQUENCIES, required=False) or "one_time",
    }
