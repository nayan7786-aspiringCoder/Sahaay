"""Storage layer.

Two interchangeable stores behind one interface:
  - SheetsStore  — Google Sheets API v4 via a service account (the configured backend)
  - SqliteStore  — zero-setup local file, so the project runs offline (demo/presentation)

get_store() picks the active store once per process:
  STORE_MODE=sheets|sqlite forces one; auto uses Sheets when credentials exist and
  answers, otherwise falls back to SQLite and logs why.
"""
import logging

from sahaay import config

logger = logging.getLogger("sahaay")
_store = None


class BaseStore:
    kind = "base"

    # providers
    def list_providers(self) -> list[dict]: raise NotImplementedError
    def get_provider(self, provider_id: str) -> dict | None: raise NotImplementedError
    def insert_provider(self, provider: dict) -> dict: raise NotImplementedError
    def update_provider(self, provider_id: str, patch: dict) -> dict | None: raise NotImplementedError

    # bookings
    def list_bookings(self, provider_id: str | None = None) -> list[dict]: raise NotImplementedError
    def get_booking(self, booking_id: str) -> dict | None: raise NotImplementedError
    def insert_booking(self, booking: dict) -> dict: raise NotImplementedError
    def update_booking(self, booking_id: str, patch: dict) -> dict | None: raise NotImplementedError

    # maintenance
    def clear_all(self) -> None: raise NotImplementedError
    def ping(self) -> None: raise NotImplementedError
    def describe(self) -> str: raise NotImplementedError


def get_store() -> BaseStore:
    global _store
    if _store is not None:
        return _store

    mode = config.store_mode_resolved()
    if mode == "sheets":
        try:
            from sahaay.sheets_store import SheetsStore

            store = SheetsStore()
            store.ping()
            _store = store
            logger.info("Sahaay store: Google Sheets (%s)", store.describe())
            return _store
        except Exception as exc:  # perms, bad key, network down…
            logger.warning("Google Sheets store unavailable (%s); using SQLite fallback.", exc)
            if config.STORE_MODE == "sheets":
                raise  # explicit STORE_MODE=sheets must not hide the failure

    from sahaay.sqlite_store import SqliteStore

    _store = SqliteStore()
    logger.info("Sahaay store: SQLite (%s)", _store.describe())
    return _store
