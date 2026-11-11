"""Criterion: Provider registration: tradesperson.

Registering an electrician/carpenter/other with name, phone, specialty, and
shop address; the public profile afterwards shows the real phone and shop
address.
"""

import uuid

import pytest


@pytest.mark.parametrize("category", ["electrician", "carpenter", "other"])
def test_register_tradesperson_shows_real_phone_and_address(client, category):
    name = f"tscheck-trade-{category}-{uuid.uuid4().hex[:8]}"
    payload = {
        "category": category,
        "name": name,
        "phone": "9123456780",
        "specialty": "General repair work",
        "shop_address": "12 Test Market Road, Testville",
    }
    resp = client.post("/providers", json=payload)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    provider_id = created["id"]

    detail = client.get(f"/providers/{provider_id}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["phone"] == "+919123456780" or body["phone"].endswith("9123456780")
    assert body["shop_address"] == "12 Test Market Road, Testville"
    assert body["category"] == category
