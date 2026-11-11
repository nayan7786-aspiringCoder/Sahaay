"""Timetable domain logic — shared by the timetable endpoint and booking checks.

Slots are hourly on the grid 06:00 → 21:00.
A booking blocks slots according to its frequency:
  - one_time: only on its date
  - daily:    every day
  - weekly:   every week on its weekday
"""

from sahaay.validation import GRID_END_HOUR, GRID_START_HOUR, MORNING_END


def hour_slots() -> list[tuple[str, str]]:
    return [(f"{h:02d}:00", f"{h + 1:02d}:00") for h in range(GRID_START_HOUR, GRID_END_HOUR)]


def slot_period(slot_start: str) -> str:
    return "morning" if slot_start < MORNING_END else "evening"


def add_hour(slot_start: str) -> str:
    hour, minute = slot_start.split(":")
    return f"{(int(hour) + 1) % 24:02d}:{minute}"


def window_covers(provider: dict, period: str, start: str, end: str) -> bool:
    available = provider.get(f"{period}_available")
    w_start = provider.get(f"{period}_start")
    w_end = provider.get(f"{period}_end")
    return bool(available and w_start and w_end and w_start <= start and end <= w_end)


def booking_blocks(booking: dict, date_str: str, weekday: int, start: str, end: str) -> bool:
    """Does this active booking block the given slot on the given date?"""
    if booking.get("status") != "accepted":
        return False
    if booking["slot_start"] >= end or start >= booking["slot_end"]:
        return False  # no time overlap
    frequency = booking.get("frequency")
    if frequency == "one_time":
        return booking["date"] == date_str
    if frequency == "daily":
        return True
    if frequency == "weekly":
        return int(booking.get("weekday", weekday)) == weekday
    return False


def slot_status(provider: dict, bookings: list[dict], date_str: str, weekday: int,
                start: str, end: str) -> str:
    if any(booking_blocks(b, date_str, weekday, start, end) for b in bookings):
        return "booked"
    return "available" if window_covers(provider, slot_period(start), start, end) else "unavailable"


def build_timetable(provider: dict, bookings: list[dict], date_str: str, weekday: int) -> dict:
    slots = [
        {
            "start": start,
            "end": end,
            "period": slot_period(start),
            "status": slot_status(provider, bookings, date_str, weekday, start, end),
        }
        for start, end in hour_slots()
    ]
    return {"provider": provider, "date": date_str, "weekday": weekday, "slots": slots}
