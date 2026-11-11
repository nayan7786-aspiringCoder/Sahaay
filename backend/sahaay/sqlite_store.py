"""SQLite store — zero-setup local fallback.

Used automatically when Google Sheets credentials are absent or unreachable
(e.g. an offline presentation). Same rows, same columns as the Sheets tabs.
"""
import sqlite3

from sahaay.config import SQLITE_PATH
from sahaay.storage import BaseStore

PROVIDER_COLS = [
    "id", "name", "category", "specialty", "work_type", "phone", "shop_address",
    "morning_available", "morning_start", "morning_end",
    "evening_available", "evening_start", "evening_end",
    "wants_regular", "verified", "created_at",
]
BOOKING_COLS = [
    "id", "provider_id", "consumer_name", "consumer_phone", "date", "weekday",
    "period", "slot_start", "slot_end", "frequency", "status", "created_at",
]
BOOL_COLS = {"morning_available", "evening_available", "wants_regular", "verified"}
INT_COLS = {"weekday"}

DDL = f"""
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
    specialty TEXT NOT NULL DEFAULT '', work_type TEXT, phone TEXT NOT NULL,
    shop_address TEXT,
    morning_available INTEGER NOT NULL DEFAULT 0, morning_start TEXT, morning_end TEXT,
    evening_available INTEGER NOT NULL DEFAULT 0, evening_start TEXT, evening_end TEXT,
    wants_regular INTEGER NOT NULL DEFAULT 0, verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, consumer_name TEXT NOT NULL,
    consumer_phone TEXT NOT NULL, date TEXT NOT NULL, weekday INTEGER NOT NULL,
    period TEXT NOT NULL, slot_start TEXT NOT NULL, slot_end TEXT NOT NULL,
    frequency TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookings_provider ON bookings(provider_id);
"""


def _to_doc(row: sqlite3.Row) -> dict:
    doc = dict(row)
    for key, value in doc.items():
        if key in BOOL_COLS:
            doc[key] = bool(value)
        elif key in INT_COLS:
            doc[key] = int(value or 0)
        elif value is None:
            doc[key] = None
    return doc








def _values(doc: dict, cols: list[str]) -> list:
    """Row values in column order; booleans/ints coerced so NOT NULL columns never get None."""
    return [int(bool(doc.get(c))) if c in BOOL_COLS
            else int(doc.get(c) or 0) if c in INT_COLS
            else doc.get(c) for c in cols]


class SqliteStore(BaseStore):
    kind = "sqlite"

    def __init__(self, path=None):
        self.path = str(path or SQLITE_PATH)
        from pathlib import Path

        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(DDL)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def describe(self) -> str:
        return f"sqlite://{self.path}"

    def ping(self) -> None:
        with self._conn() as conn:
            conn.execute("SELECT 1").fetchone()

    # ---- providers ----
    def list_providers(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM providers ORDER BY created_at DESC").fetchall()
        return [_to_doc(r) for r in rows]

    def get_provider(self, provider_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone()
        return _to_doc(row) if row else None

    def insert_provider(self, provider: dict) -> dict:
        cols = PROVIDER_COLS
        values = _values(provider, cols)
        with self._conn() as conn:
            conn.execute(
                f"INSERT INTO providers ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                values,
            )
        return provider

    def update_provider(self, provider_id: str, patch: dict) -> dict | None:
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        provider.update(patch)
        with self._conn() as conn:
            conn.execute(
                f"UPDATE providers SET {', '.join(f'{c} = ?' for c in PROVIDER_COLS)} WHERE id = ?",
                _values(provider, PROVIDER_COLS) + [provider_id],
            )
        return provider

    # ---- bookings ----
    def list_bookings(self, provider_id: str | None = None) -> list[dict]:
        with self._conn() as conn:
            if provider_id:
                rows = conn.execute(
                    "SELECT * FROM bookings WHERE provider_id = ? ORDER BY created_at DESC",
                    (provider_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
        return [_to_doc(r) for r in rows]

    def get_booking(self, booking_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        return _to_doc(row) if row else None

    def insert_booking(self, booking: dict) -> dict:
        cols = BOOKING_COLS
        with self._conn() as conn:
            conn.execute(
                f"INSERT INTO bookings ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                _values(booking, cols),
            )
        return booking

    def update_booking(self, booking_id: str, patch: dict) -> dict | None:
        booking = self.get_booking(booking_id)
        if not booking:
            return None
        booking.update(patch)
        with self._conn() as conn:
            conn.execute(
                f"UPDATE bookings SET {', '.join(f'{c} = ?' for c in BOOKING_COLS)} WHERE id = ?",
                _values(booking, BOOKING_COLS) + [booking_id],
            )
        return booking

    def clear_all(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM bookings")
            conn.execute("DELETE FROM providers")
