"""Criterion: Booking request + recurring (API-depth part).

A weekly booking shows as booked on the same weekday the following week;
a daily booking shows as booked on every day. The browser check
`booking-request-recurring` covers the UI flow within the visible 7-day
strip; this test reaches beyond that window via the timetable API.
"""

from datetime import datetime, timedelta

import pytest


def _fresh_maid(client, suffix):
    payload = {
        "name": f"tscheck-maid-recurring-{suffix}",
        "phone": "9988002233",
        "category": "maid",
        "work_type": "cleaning",
        "morning_available": True,
        "morning_start": "09:00",
        "morning_end": "12:00",
        "evening_available": False,
        "wants_regular": True,
    }
    resp = client.post("/providers", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _today(client):
    resp = client.get("/meta")
    assert resp.status_code == 200
    return resp.json()["today"]


def test_weekly_booking_blocks_same_weekday_next_week(client):
    maid = _fresh_maid(client, "weekly")
    today = _today(client)
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    next_week = (today_dt + timedelta(days=7)).strftime("%Y-%m-%d")

    booking = client.post(
        "/bookings",
        json={
            "provider_id": maid["id"],
            "date": today,
            "slot_start": "10:00",
            "consumer_name": "tscheck-consumer-weekly",
            "consumer_phone": "9876500011",
            "frequency": "weekly",
        },
    )
    assert booking.status_code == 201, booking.text
    booking_id = booking.json()["id"]

    try:
        timetable = client.get(f"/providers/{maid['id']}/timetable", params={"date": next_week})
        assert timetable.status_code == 200, timetable.text
        slots = {s["start"]: s["status"] for s in timetable.json()["slots"]}
        assert slots["10:00"] == "booked"
        # a different hour must remain untouched
        assert slots["09:00"] == "available"
    finally:
        client.patch(f"/bookings/{booking_id}", json={"status": "cancelled"})


def test_daily_booking_blocks_every_day(client):
    maid = _fresh_maid(client, "daily")
    today = _today(client)
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    tomorrow = (today_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    plus_three = (today_dt + timedelta(days=3)).strftime("%Y-%m-%d")

    booking = client.post(
        "/bookings",
        json={
            "provider_id": maid["id"],
            "date": today,
            "slot_start": "11:00",
            "consumer_name": "tscheck-consumer-daily",
            "consumer_phone": "9876500022",
            "frequency": "daily",
        },
    )
    assert booking.status_code == 201, booking.text
    booking_id = booking.json()["id"]

    try:
        for d in (tomorrow, plus_three):
            timetable = client.get(f"/providers/{maid['id']}/timetable", params={"date": d})
            assert timetable.status_code == 200, timetable.text
            slots = {s["start"]: s["status"] for s in timetable.json()["slots"]}
            assert slots["11:00"] == "booked", f"expected 11:00 booked on {d}"
    finally:
        client.patch(f"/bookings/{booking_id}", json={"status": "cancelled"})
