"""Criterion: No double booking + API errors.

POST /api/bookings:
- already-booked slot -> 409 {error:{code:'SLOT_ALREADY_BOOKED'}}
- booking a tradesperson -> 400 NOT_BOOKABLE
- slot outside maid's hours -> 400 SLOT_NOT_OFFERED
- unknown provider id -> 404
"""

import uuid

import pytest


MAID_NAME = "Sunita Devi"
FUTURE_DATE = "2026-12-21"  # a Monday far enough in future, not seeded


def _find_provider(client, category, name=None):
    resp = client.get("/providers", params={"category": category})
    assert resp.status_code == 200, resp.text
    providers = resp.json()["providers"]
    if name:
        for p in providers:
            if p["name"] == name:
                return p
    return providers[0]


@pytest.fixture
def maid(client):
    return _find_provider(client, "maid", MAID_NAME)


@pytest.fixture
def electrician(client):
    return _find_provider(client, "electrician")


def _booking_payload(provider_id, date_, start, frequency="one_time"):
    return {
        "provider_id": provider_id,
        "date": date_,
        "slot_start": start,
        "consumer_name": f"tscheck-customer-{uuid.uuid4().hex[:8]}",
        "consumer_phone": "9876543210",
        "frequency": frequency,
    }


def test_double_booking_returns_409(client, maid):
    # Sunita Devi is morning 07:00-11:00. Book a fresh slot on a future date.
    payload = _booking_payload(maid["id"], FUTURE_DATE, "09:00")
    created = client.post("/bookings", json=payload)
    assert created.status_code == 201, created.text
    booking_id = created.json()["id"]

    try:
        dupe = client.post("/bookings", json=payload)
        assert dupe.status_code == 409, dupe.text
        body = dupe.json()
        assert body["error"]["code"] == "SLOT_ALREADY_BOOKED"
    finally:
        client.patch(f"/bookings/{booking_id}", json={"status": "cancelled"})


def test_booking_tradesperson_returns_400_not_bookable(client, electrician):
    payload = _booking_payload(electrician["id"], FUTURE_DATE, "09:00")
    resp = client.post("/bookings", json=payload)
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "NOT_BOOKABLE"


def test_booking_outside_maid_hours_returns_400_slot_not_offered(client, maid):
    # Sunita is morning only (07:00-11:00); 18:00 is outside her offered hours.
    payload = _booking_payload(maid["id"], FUTURE_DATE, "18:00")
    resp = client.post("/bookings", json=payload)
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "SLOT_NOT_OFFERED"


def test_booking_unknown_provider_returns_404(client):
    payload = _booking_payload(str(uuid.uuid4()), FUTURE_DATE, "09:00")
    resp = client.post("/bookings", json=payload)
    assert resp.status_code == 404, resp.text
