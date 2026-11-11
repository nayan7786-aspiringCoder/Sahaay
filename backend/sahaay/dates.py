"""Server-side date/time helpers.

The pod clock is UTC; Sahaay's users think in IST, so "today" is anchored here
(APP_TIMEZONE, default Asia/Kolkata) — never with client-side date math.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return now_utc().isoformat()


def tznow(tz_name: str | None = None) -> datetime:
    from sahaay.config import APP_TIMEZONE

    return datetime.now(ZoneInfo(tz_name or APP_TIMEZONE))


def today_iso(tz_name: str | None = None) -> str:
    return tznow(tz_name).date().isoformat()


def weekday_of(date_str: str) -> int:
    """0 = Monday ... 6 = Sunday."""
    return datetime.strptime(date_str, "%Y-%m-%d").date().weekday()


def week_strip(days: int = 7, tz_name: str | None = None) -> list[dict]:
    """The next `days` days, server-anchored: [{date, weekday, label}]."""
    start = tznow(tz_name).date()
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        out.append({"date": d.isoformat(), "weekday": d.weekday(), "label": d.strftime("%a %d")})
    return out
