# Sahaay backend (Python Flask)

REST API under `/api` — providers, search, timetables, bookings.
Detailed docs live in the project root: [`../README.md`](../README.md),
[`../docs/API.md`](../docs/API.md), [`../docs/DATABASE.md`](../docs/DATABASE.md).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python seed.py          # demo data (idempotent; --force to wipe) — SQLite mode needs no Google setup
python server.py        # http://localhost:8001  (dev)

# production
gunicorn -w 2 -b 0.0.0.0:8001 server:flask_app
```

```
sahaay/
├── config.py         # env config (backend/.env via python-dotenv)
├── errors.py         # consistent {"error": {...}} responses
├── validation.py     # input validation & cleaning
├── timetable.py      # slot grid + booking-conflict rules
├── storage.py        # store interface + Sheets/SQLite selection
├── sheets_store.py   # Google Sheets API v4
├── sqlite_store.py   # offline SQLite store
├── dates.py          # server-anchored "today" (IST default)
└── routes/           # /api endpoints: meta, providers, bookings
seed.py               # demo data
setup_sheets.py       # creates the spreadsheet tabs + headers
```

Configuration comes from environment variables (see `.env.example`).
Credentials are never hardcoded — `GOOGLE_SERVICE_ACCOUNT_JSON` accepts a raw
JSON string or a key-file path, `GOOGLE_SHEETS_ID` selects the spreadsheet.
