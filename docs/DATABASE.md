# Database setup & schema

Sahaay stores everything as simple rows — either in **Google Sheets** (the
configured cloud store) or in a local **SQLite** file (offline fallback). Both
implement the same tiny interface (`backend/sahaay/storage.py`), so the REST
API behaves identically in either mode.

```
backend/sahaay/storage.py     # interface + selection
backend/sahaay/sheets_store.py  # Google Sheets API v4 (service account)
backend/sahaay/sqlite_store.py  # SQLite file backend/data/sahaay.db
```

Which store is active? `GET /api/health` → `"store"`.
`STORE_MODE=auto` (default): Sheets when `GOOGLE_SHEETS_ID` and
`GOOGLE_SERVICE_ACCOUNT_JSON` are set **and** reachable, else SQLite.
Force one with `STORE_MODE=sheets` or `STORE_MODE=sqlite`.

## Google Sheets setup (tabs + headers)

Share your spreadsheet with the service-account email as **Editor**, then run:

```bash
cd backend && python setup_sheets.py
```

The script creates the two tabs below with exactly these headers (row 1,
frozen) if they don't already exist, and prints the service-account email as a
reminder. No other spreadsheet structure is required — data starts at row 2.

### Tab `Providers` — 16 columns, in order

| # | Column | Type / values | Notes |
|---|---|---|---|
| 1 | `id` | uuid string | Primary key |
| 2 | `name` | text | Provider name |
| 3 | `category` | `maid` \| `electrician` \| `carpenter` \| `other` | |
| 4 | `specialty` | text | Maids: derived from work type; trades: free text |
| 5 | `work_type` | `cleaning` \| `cooking` \| `both` *(blank for trades)* | |
| 6 | `phone` | `+91XXXXXXXXXX` | Maids: masked in public API responses |
| 7 | `shop_address` | text *(trades only)* | Public |
| 8 | `morning_available` | `true`/`false` | |
| 9 | `morning_start` | `HH:MM` | |
| 10 | `morning_end` | `HH:MM` | |
| 11 | `evening_available` | `true`/`false` | |
| 12 | `evening_start` | `HH:MM` | |
| 13 | `evening_end` | `HH:MM` | |
| 14 | `wants_regular` | `true`/`false` | Maids' recurring-work preference |
| 15 | `verified` | `true`/`false` | Safe placeholder — **no Aadhaar/ID columns exist** |
| 16 | `created_at` | ISO datetime | |

### Tab `Bookings` — 12 columns, in order

| # | Column | Type / values | Notes |
|---|---|---|---|
| 1 | `id` | uuid string | Primary key |
| 2 | `provider_id` | uuid | FK → `Providers.id` |
| 3 | `consumer_name` | text | |
| 4 | `consumer_phone` | `+91XXXXXXXXXX` | |
| 5 | `date` | `YYYY-MM-DD` | Anchor date of the request |
| 6 | `weekday` | 0–6 | 0 = Monday (drives `weekly` recurrence) |
| 7 | `period` | `morning` \| `evening` | |
| 8 | `slot_start` | `HH:MM` | Hourly grid 06:00–21:00 |
| 9 | `slot_end` | `HH:MM` | start + 1 h |
| 10 | `frequency` | `one_time` \| `daily` \| `weekly` | Recurrence model |
| 11 | `status` | `accepted` \| `declined` \| `cancelled` | New bookings are auto-`accepted` |
| 12 | `created_at` | ISO datetime | |

## SQLite schema (offline fallback)

Same columns, typed natively; booleans are `0/1`. Created automatically on
first run (`backend/data/sahaay.db`, configurable via `DATA_DIR`/`SQLITE_PATH`):

```sql
CREATE TABLE providers (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
    specialty TEXT NOT NULL DEFAULT '', work_type TEXT, phone TEXT NOT NULL,
    shop_address TEXT,
    morning_available INTEGER NOT NULL DEFAULT 0, morning_start TEXT, morning_end TEXT,
    evening_available INTEGER NOT NULL DEFAULT 0, evening_start TEXT, evening_end TEXT,
    wants_regular INTEGER NOT NULL DEFAULT 0, verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE bookings (
    id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, consumer_name TEXT NOT NULL,
    consumer_phone TEXT NOT NULL, date TEXT NOT NULL, weekday INTEGER NOT NULL,
    period TEXT NOT NULL, slot_start TEXT NOT NULL, slot_end TEXT NOT NULL,
    frequency TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX idx_bookings_provider ON bookings(provider_id);
```

## Slot & double-booking rules (shared logic, `backend/sahaay/timetable.py`)

- The timetable is the hourly grid **06:00 → 21:00**; slots starting before
  12:00 are *morning*, the rest *evening*.
- A slot is **green/available** only when it lies inside the provider's window
  for its period (`window_covers`) and no accepted booking blocks it.
- An accepted booking **blocks** its slot:
  `one_time` → on its `date` · `daily` → every day · `weekly` → every week on
  its `weekday`. Blocked ⇒ red; inside-no-window ⇒ grey.
- Creating (or accepting) a booking re-runs these rules and returns
  `409 SLOT_ALREADY_BOOKED` on conflict, so a booked slot can never be offered
  as free again.

## Privacy

There is **no Aadhaar / government-ID column anywhere** — none is collected,
transmitted, or stored. `verified` is a plain boolean placeholder intended to
be driven by a trusted verification provider. Maid phone numbers are masked
(`+91 98XXX XXX23`) in all public responses; the full number is attached only
to the booking record the consumer created.
