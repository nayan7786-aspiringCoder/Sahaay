# Sahaay API reference

Base URL: `http://localhost:8001/api` (dev) — the frontend calls these as
relative `/api/...` paths through its typed fetch layer.

All errors share one shape:

```json
{ "error": { "code": "SLOT_ALREADY_BOOKED", "message": "…", "details": [] } }
```

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Missing/invalid fields (details list the field names) |
| 400 | `SLOT_NOT_OFFERED` | Slot outside the provider's availability |
| 400 | `NOT_BOOKABLE` | Timetable booking attempted on a non-maid provider |
| 400 | `BAD_REQUEST` / `INVALID_JSON`-style | Malformed body |
| 404 | `PROVIDER_NOT_FOUND` / `BOOKING_NOT_FOUND` | Unknown id |
| 405 | `METHOD_NOT_ALLOWED` | Wrong HTTP method |
| 409 | `SLOT_ALREADY_BOOKED` | Slot already blocked by an accepted booking |
| 409 | `BOOKING_CLOSED` | Accept on a declined/cancelled booking |
| 502 | `SHEETS_ERROR` | Google Sheets API failure (permissions, id, network) |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## GET /api/health

```bash
curl http://localhost:8001/api/health
```

```json
{
  "status": "ok",
  "store": "google-sheets",
  "store_detail": "google-sheets://1AbC…",
  "sheets_configured": true,
  "time": "2026-11-10T16:20:41.123456+00:00"
}
```

Without Google credentials: `"store": "sqlite"` (offline mode).

## GET /api/meta

Category/label catalogues plus a **server-anchored** 7-day strip used by the
timetable day selector (never computed client-side).

```bash
curl "http://localhost:8001/api/meta"
```

```json
{
  "categories": [
    { "id": "maid", "label": "Maid" },
    { "id": "electrician", "label": "Electrician" },
    { "id": "carpenter", "label": "Carpenter" },
    { "id": "other", "label": "Other Local Service" }
  ],
  "work_types": [
    { "id": "cleaning", "label": "House cleaning" },
    { "id": "cooking", "label": "Cooking" },
    { "id": "both", "label": "Cleaning & Cooking" }
  ],
  "frequencies": [
    { "id": "one_time", "label": "One-time service" },
    { "id": "daily", "label": "Daily recurring" },
    { "id": "weekly", "label": "Weekly recurring" }
  ],
  "bookings_auto_accept": true,
  "today": "2026-11-10",
  "week": [
    { "date": "2026-11-10", "weekday": 1, "label": "Tue 10" }
  ],
  "store": "google-sheets"
}
```

## POST /api/providers — register

**Maid** (morning/evening availability + regular-work preference):

```bash
curl -X POST http://localhost:8001/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sunita Devi",
    "phone": "9826011223",
    "category": "maid",
    "work_type": "cleaning",
    "morning_available": true, "morning_start": "07:00", "morning_end": "11:00",
    "evening_available": false,
    "wants_regular": true
  }'
```

`201 Created` — public profile (maid phones are masked; the plain `phone`
field is deliberately absent for maids):

```json
{
  "id": "6f0d3f5e-…",
  "name": "Sunita Devi",
  "category": "maid",
  "specialty": "House cleaning",
  "work_type": "cleaning",
  "phone_masked": "+91 98XXX XXX23",
  "shop_address": null,
  "morning_available": true, "morning_start": "07:00", "morning_end": "11:00",
  "evening_available": false, "evening_start": null, "evening_end": null,
  "wants_regular": true,
  "verified": false,
  "created_at": "2026-11-10T16:21:02.512…+00:00"
}
```

**Tradesperson** (phone + shop address are public by design):

```bash
curl -X POST http://localhost:8001/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vijay Electric Works",
    "phone": "9425066778",
    "category": "electrician",
    "specialty": "House wiring, inverter & MCB repair",
    "shop_address": "5, Bhawarkuan Main Road, Indore"
  }'
```

`201` returns the profile with a real `phone` and `shop_address`.

Validation failures return `400 VALIDATION_ERROR`, e.g. bad phone:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Enter a valid Indian mobile number (10 digits, optional +91).",
    "details": [{ "field": "phone" }]
  }
}
```

## GET /api/providers — search & filter

Query params (all optional, combinable):
`category` (maid/electrician/carpenter/other) · `work_type`
(cleaning/cooking/both, maids) · `shift` (morning/evening) ·
`regular=true|false` (maids' recurring preference) · `q` (name/specialty text).

```bash
curl "http://localhost:8001/api/providers?category=maid&work_type=cooking&shift=morning&regular=true"
curl "http://localhost:8001/api/providers?category=electrician"
curl "http://localhost:8001/api/providers?q=wiring"
```

```json
{
  "providers": [ { "id": "…", "name": "Kamla Sharma", "category": "maid", "…": "…" } ],
  "count": 1
}
```

## GET /api/providers/{id} — public profile

```bash
curl http://localhost:8001/api/providers/6f0d3f5e-…
```

Same shape as registration. `404` for unknown ids.

## PATCH /api/providers/{id} — availability & listing updates

```bash
curl -X PATCH http://localhost:8001/api/providers/6f0d3f5e-… \
  -H "Content-Type: application/json" \
  -d '{ "evening_available": true, "evening_start": "17:00", "evening_end": "20:00" }'
```

Returns the updated public profile. Accepts any of: `morning_available`,
`morning_start`, `morning_end`, `evening_available`, `evening_start`,
`evening_end`, `wants_regular`, `specialty`, `shop_address`.

## GET /api/providers/{id}/timetable — maid day timetable

```bash
curl "http://localhost:8001/api/providers/6f0d3f5e-…/timetable?date=2026-11-12"
```

`date` is optional (defaults to *today*, anchored on the server). Hourly slots
run 06:00–21:00; `status` is `available` (green, tappable), `booked` (red) or
`unavailable` (grey):

```json
{
  "provider": { "id": "6f0d3f5e-…", "name": "Sunita Devi", "phone_masked": "+91 98XXX XXX23", "…": "…" },
  "date": "2026-11-12",
  "weekday": 3,
  "slots": [
    { "start": "06:00", "end": "07:00", "period": "morning", "status": "unavailable" },
    { "start": "07:00", "end": "08:00", "period": "morning", "status": "booked" },
    { "start": "08:00", "end": "09:00", "period": "morning", "status": "available" }
  ]
}
```

## POST /api/bookings — create (auto-accepted)

```bash
curl -X POST http://localhost:8001/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "6f0d3f5e-…",
    "date": "2026-11-12",
    "slot_start": "08:00",
    "consumer_name": "Rohit Verma",
    "consumer_phone": "9039010101",
    "frequency": "weekly"
  }'
```

- Slots are hourly on the hour; `frequency` ∈ `one_time` (default) | `daily` | `weekly`.
- Bookings are **auto-accepted**; the slot immediately stops being offered.
- `201 Created` — includes the provider's real phone (revealed to the consumer
  who booked):

```json
{
  "id": "b71c…",
  "provider_id": "6f0d3f5e-…",
  "provider_name": "Sunita Devi",
  "provider_phone": "+919826011223",
  "consumer_name": "Rohit Verma",
  "consumer_phone": "+919039010101",
  "date": "2026-11-12",
  "weekday": 3,
  "period": "morning",
  "slot_start": "08:00",
  "slot_end": "09:00",
  "frequency": "weekly",
  "status": "accepted",
  "created_at": "2026-11-10T16:24:09.812…+00:00"
}
```

Double-booking → `409`:

```json
{
  "error": {
    "code": "SLOT_ALREADY_BOOKED",
    "message": "08:00–09:00 is already booked for 2026-11-12 (weekly). Please pick another green slot.",
    "details": [{ "slot_start": "08:00", "slot_end": "09:00", "date": "2026-11-12", "frequency": "weekly" }]
  }
}
```

## GET /api/bookings · GET /api/bookings/{id}

```bash
curl "http://localhost:8001/api/bookings?provider_id=6f0d3f5e-…"
curl http://localhost:8001/api/bookings/b71c…
```

```json
{ "bookings": [ { "…": "…" } ], "count": 1 }
```

## PATCH /api/bookings/{id} — update / cancel

Updatable: `date`, `slot_start`, `frequency`, `status`
(`accepted`/`declined`/`cancelled`). Time changes re-run availability and
conflict checks. Cancelling or rejecting frees the slot (grey/green again).

```bash
curl -X PATCH http://localhost:8001/api/bookings/b71c… \
  -H "Content-Type: application/json" \
  -d '{ "status": "cancelled" }'
```

## POST /api/bookings/{id}/accept · /reject

Idempotent provider-decision endpoints (kept for a future provider-managed
flow; the UI auto-accepts today). `accept` re-checks conflicts and returns
`409 SLOT_ALREADY_BOOKED` if the slot was taken meanwhile.

```bash
curl -X POST http://localhost:8001/api/bookings/b71c…/accept
curl -X POST http://localhost:8001/api/bookings/b71c…/reject
```
