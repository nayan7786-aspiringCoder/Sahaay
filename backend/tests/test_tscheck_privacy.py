"""Criterion: Privacy — maid public profile masks phone, no Aadhaar/ID field
anywhere, tradesperson profiles expose real phone + shop_address."""


def test_maid_public_profile_masks_phone(client):
    resp = client.get("/providers", params={"category": "maid"})
    assert resp.status_code == 200, resp.text
    providers = resp.json()["providers"]
    assert len(providers) > 0
    maid = providers[0]
    assert "phone_masked" in maid
    assert maid["phone_masked"].startswith("+91")
    assert "XXX" in maid["phone_masked"]
    assert "phone" not in maid
    assert "aadhaar" not in {k.lower() for k in maid.keys()}
    assert not any("aadhaar" in k.lower() or k.lower() == "id_number" for k in maid.keys())

    # Full provider detail (GET /providers/{id}) must also mask phone for maids
    detail = client.get(f"/providers/{maid['id']}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert "phone" not in body
    assert "phone_masked" in body
    assert not any("aadhaar" in k.lower() for k in body.keys())


def test_tradesperson_profile_has_real_phone_and_shop_address(client):
    resp = client.get("/providers", params={"category": "electrician"})
    assert resp.status_code == 200, resp.text
    providers = resp.json()["providers"]
    assert len(providers) > 0
    trade = providers[0]
    assert "phone" in trade
    assert trade["phone"]
    assert "shop_address" in trade
    assert trade["shop_address"]
    assert not any("aadhaar" in k.lower() for k in trade.keys())

    detail = client.get(f"/providers/{trade['id']}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body.get("phone")
    assert body.get("shop_address")
