# Sahaay — Local Services Platform

Find trusted local service providers — **maids** (with a live, bookable
morning/evening timetable), **electricians**, **carpenters** and other
neighbourhood helpers. Households browse and book; providers register in under
a minute. No Aadhaar, ever.

- **Backend** — Python **Flask**, REST API under `/api`
  (`backend/`, served by uvicorn/gunicorn)
- **Frontend** — React 19 + Vite + TypeScript + Tailwind v4 (`frontend/`)
- **Storage** — **Google Sheets API** (service account) when configured,
  with an automatic **SQLite** fallback so the project also runs fully offline

---

## Features

| Area | What you get |
|---|---|
| First screen | Two clear paths: **"I provide a service"** / **"I'm looking for a service"** |
| Provider registration | Category-aware forms — maids (work type, morning/evening hours, regular-work preference) vs tradespeople (specialty, phone, shop address) |
| Consumer search | Filter by category, work type/specialty, morning/evening shift, regular-work preference, free-text search |
| Maid timetable | Hourly slot grid for the selected day — **green = available (tap to book)**, **red = booked/busy**, **grey = off-duty** |
| Recurring work | Bookings can be one-time, **daily** or **weekly**; recurring bookings block their slot on every matching day |
| Double-booking guard | Once a slot is booked it never re-appears as free; conflicts return a clean `409` |
| Privacy by design | No Aadhaar/government IDs collected; maid phone numbers are masked publicly and revealed only after a booking is confirmed |
| Verified badge | Safe verification placeholder (a status flag — no identity documents) |

## Architecture

```
┌────────────────────┐   relative /api requests   ┌──────────────────────┐
│  React 19 + Vite   │ ─────────────────────────► │  Flask REST API      │
│  (frontend/, :3000)│    (Vite dev proxy or      │  (backend/, :8001)   │
│  TanStack Query    │     nginx in production)   │  validation, rules   │
└────────────────────┘                            └──────────┬───────────┘
                                                             │ Google Sheets API v4
                                             ┌───────────────┴───────────────┐
                                             ▼                               ▼
                                  ┌────────────────────┐          ┌────────────────┐
                                  │ Google Sheets      │  or      │ SQLite file    │
                                  │ (service account)  │  offline │ backend/data/  │
                                  └────────────────────┘          └────────────────┘
```

The frontend **never** talks to Google Sheets directly — all reads/writes flow
through the Flask API.

## Project structure

```
sahaay/
├── backend/
│   ├── server.py              # entrypoint: Flask app wrapped for uvicorn/gunicorn
│   ├── sahaay/
│   │   ├── __init__.py        # create_app(): CORS, error handlers, blueprint
│   │   ├── config.py          # env config (loaded from backend/.env)
│   │   ├── dates.py           # server-anchored "today" (IST by default)
│   │   ├── errors.py          # consistent {"error": {...}} responses
│   │   ├── validation.py      # input validation & cleaning
│   │   ├── timetable.py       # slot grid + booking-conflict logic
│   │   ├── storage.py         # store interface + selection (Sheets/SQLite)
│   │   ├── sheets_store.py    # Google Sheets API v4 implementation
│   │   ├── sqlite_store.py    # offline SQLite implementation
│   │   └── routes/            # REST endpoints (meta, providers, bookings)
│   ├── seed.py                # demo data (idempotent; --force to wipe)
│   ├── setup_sheets.py        # creates the spreadsheet tabs + headers
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── lib/api.ts         # typed fetch helpers over relative /api paths
│       ├── lib/types.ts       # TS mirrors of every backend JSON shape
│       ├── components/        # SiteHeader, ProviderCard, TimetableGrid, BookingDialog
│       └── pages/             # Home, Browse, ProviderDetail, Register, NotFound
├── docs/API.md                # full API reference with examples
├── docs/DATABASE.md           # sheet tabs, columns, SQLite schema
├── Dockerfile.backend / Dockerfile.frontend / nginx.conf / docker-compose.yml
```

## Offline presentation (one command, Python only)

The repo ships a prebuilt website in `frontend/dist`, and Flask serves it, so
you don't need Node.js on presentation day.

1. **Once, while online:** install Python 3.10+ and run the launcher. It
   creates `backend/.venv`, installs the packages, and loads the demo data.
   - Windows: double-click `start_offline.bat`
   - macOS/Linux: `./start_offline.sh`
2. **During the presentation (no internet needed):** run the same launcher
   again. The site opens at **http://localhost:8001**.

The downloaded code contains no Google keys, so offline it uses a local SQLite
database (`backend/data/sahaay.db`) with the demo data. To use Google Sheets
locally, add your keys to `backend/.env` (see *Google Sheets setup*).
If you change the frontend code, rebuild it with `cd frontend && yarn build`.

## Run locally for development (two terminals)

```bash
# 1) Backend
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                 # demo providers + bookings (works with no Google config)
python server.py               # Flask dev server → http://localhost:8001

# 2) Frontend (second terminal)
cd frontend
yarn install                   # or: npm install
yarn dev                       # → http://localhost:3000 (proxies /api → :8001)
```

**No internet / no Google account needed:** without Google credentials the
backend automatically uses a local SQLite file (`backend/data/sahaay.db`) —
perfect for an offline presentation. It switches to Google Sheets as soon as
credentials are configured (see below).

## Google Sheets setup

1. **Create a Google Cloud project** → [console.cloud.google.com](https://console.cloud.google.com)
2. **Enable the Google Sheets API** — *APIs & Services → Library → Google Sheets API → Enable*
3. **Create a service account** — *IAM & Admin → Service Accounts → Create*; then
   *Keys → Add key → JSON* and download the key file.
4. **Create the spreadsheet** (a blank one is fine) and **share it with the
   service account's email** (`…@…iam.gserviceaccount.com`) as **Editor**.
5. **Configure credentials — never in source code.** Create `backend/.env`:

   ```bash
   GOOGLE_SHEETS_ID=1AbC…your-spreadsheet-id…    # from the sheet's URL
   GOOGLE_SERVICE_ACCOUNT_JSON=./secrets/service-account.json   # path or raw JSON
   STORE_MODE=auto                               # sheets | sqlite | auto
   CORS_ORIGINS=*
   APP_TIMEZONE=Asia/Kolkata
   ```

6. **Create the tabs & headers**:

   ```bash
   cd backend && python setup_sheets.py
   ```

   This creates (if missing) the `Providers` and `Bookings` tabs with the exact
   column headers the API expects, and freezes row 1. Column layout is in
   [docs/DATABASE.md](docs/DATABASE.md).
7. **Seed & restart** — `python seed.py` now writes through the Sheets API.
   Verify anytime at `GET /api/health` (`"store": "google-sheets"`).

Keep the key file out of version control (`.gitignore` already excludes
`backend/.env` and key files). Rotate the key if it ever leaves your machine.

## How the frontend uses the Flask APIs

- Every request goes through `frontend/src/lib/api.ts` — thin typed helpers
  (`apiGet/apiPost/apiPatch`) over **relative** `/api/...` paths. In dev, Vite
  proxies `/api` to `localhost:8001`; in production nginx does the same, so the
  same code runs in both.
- Data is fetched with **TanStack Query** (`useQuery`/`useMutation`) — no
  ad-hoc `fetch` in components, no data in `useEffect`. After a booking
  mutation, the affected query keys are invalidated so the timetable slot turns
  red immediately.
- Response shapes are hand-written TS interfaces in `lib/types.ts`, kept in
  sync with the Flask JSON payloads (there is no cross-language inference).
- Failures degrade gracefully: if the backend is unreachable, pages still
  render their shell with skeleton/dash placeholders instead of error screens.

## API summary

| Method & path | Purpose |
|---|---|
| `GET /api/health` | Service + active store status |
| `GET /api/meta` | Categories, labels, server-anchored week strip |
| `POST /api/providers` | Register provider (maid or tradesperson) |
| `GET /api/providers` | Search & filter (`category`, `work_type`, `shift`, `regular`, `q`) |
| `GET /api/providers/{id}` | Public profile (maid phones masked) |
| `PATCH /api/providers/{id}` | Update availability / listing fields |
| `GET /api/providers/{id}/timetable?date=YYYY-MM-DD` | Maid day timetable with slot statuses |
| `POST /api/bookings` | Create booking request (auto-accepted; `409` if taken) |
| `GET /api/bookings` · `GET /api/bookings/{id}` | List / detail (reveals provider phone) |
| `PATCH /api/bookings/{id}` | Update or cancel a booking |
| `POST /api/bookings/{id}/accept` · `…/reject` | Accept / reject (idempotent) |

Full request/response examples: **[docs/API.md](docs/API.md)**.

## Deployment

**Docker (recommended):**

```bash
cp backend/.env.example .env      # optional: add GOOGLE_* to run on Sheets
docker compose up --build         # app on http://localhost:8080, API on :8001
```

`Dockerfile.frontend` builds the React app and serves it from nginx, which
also reverse-proxies `/api` to the backend container; `Dockerfile.backend`
runs the Flask app under gunicorn.

**Plain VM:** run the frontend build behind nginx (same `nginx.conf`) and:

```bash
cd backend && gunicorn -w 2 -b 0.0.0.0:8001 server:flask_app
```

## Tests

```bash
cd backend && pytest        # backend tests hit the live server on :8001
```

## Discussion & evaluation

**Strengths**

- Clear separation of concerns: REST API, storage abstraction, typed frontend.
- Two interchangeable stores behind one interface — cloud (Sheets) for the
  real deployment, SQLite for offline demos — with identical API behaviour.
- Honest privacy model: no sensitive IDs collected or stored; maid phone
  numbers are masked until a confirmed booking; tradespeople list only
  business contact details.
- Double-booking is prevented at booking time via the shared timetable
  conflict rules; recurring (daily/weekly) arrangements are first-class.

**Limitations (known, scoped for a mini project)**

- Google Sheets has no transactions: two consumers requesting the same slot in
  the same instant could both pass the conflict check (the second write still
  succeeds; one would need row-level locking or a transactional DB to rule it
  out). SQLite mode has the same read-check-write window.
- Recurring-conflict checking is evaluated for the requested date only — a new
  weekly booking can collide with an existing one-time booking on a *future*
  date; the timetable surfaces the conflict visually (red) but does not block
  creation.
- No consumer accounts or OTP verification of phone numbers yet; "verified" is
  a placeholder flag, intended to be wired to a trusted verification provider
  (without ever storing Aadhaar).
- Sheets-based reads cost one API round-trip per request and are rate-limited
  — fine for a demo/neighbourhood scale, not for high traffic.
- Bookings auto-accept by product decision; the accept/reject endpoints exist
  (and are idempotent) for when a provider-managed flow is wanted.
