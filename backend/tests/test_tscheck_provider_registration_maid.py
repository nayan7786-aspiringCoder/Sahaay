"""Criterion: Provider registration: maid.

Valid submission creates a maid provider; invalid phone is rejected (400)
and nothing is created.
"""

import uuid

import pytest


def _maid_payload(phone="9988776655"):
    name = f"tscheck-maid-{uuid.uuid4().hex[:8]}"
    return {
        "category": "maid",
        "name": name,
        "phone": phone,
        "work_type": "cleaning",
        "morning_available": True,
        "morning_start": "08:00",
        "morning_end": "11:00",
        "evening_available": False,
        "wants_regular": True,
    }, name


def test_register_maid_valid_phone_succeeds(client):
    payload, name = _maid_payload()
    resp = client.post("/providers", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == name
    assert body["category"] == "maid"
    assert "phone" not in body or body.get("phone_masked")
    # verify it is retrievable
    detail = client.get(f"/providers/{body['id']}")
    assert detail.status_code == 200, detail.text


def test_register_maid_invalid_phone_rejected(client):
    payload, name = _maid_payload(phone="12345")
    resp = client.post("/providers", json=payload)
    assert resp.status_code == 400, resp.text
    assert "error" in resp.json()

    # Confirm nothing was created under this name.
    search = client.get("/providers", params={"category": "maid", "q": name})
    providers = search.json().get("providers", [])
    assert not any(p["name"] == name for p in providers)
