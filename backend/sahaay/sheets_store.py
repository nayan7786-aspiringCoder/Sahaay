"""Google Sheets store — the configured backend.

All reads/writes go through the Google Sheets API v4 (service-account auth).
The frontend never talks to Google directly.

Spreadsheet layout (created by backend/setup_sheets.py):
  Tab "Providers": id | name | category | specialty | work_type | phone |
                   shop_address | morning_available | morning_start | morning_end |
                   evening_available | evening_start | evening_end |
                   wants_regular | verified | created_at
  Tab "Bookings":  id | provider_id | consumer_name | consumer_phone | date | weekday |
                   period | slot_start | slot_end | frequency | status | created_at
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from sahaay.config import GOOGLE_SHEETS_ID, SHEETS_SCOPE, service_account_info
from sahaay.errors import ApiError
from sahaay.storage import BaseStore

PROVIDERS_TAB = "Providers"
BOOKINGS_TAB = "Bookings"

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


def _cell(value) -> str:
    """Serialize a Python value to one spreadsheet cell."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _parse(rows: list[list[str]], cols: list[str]) -> list[dict]:
    docs = []
    for offset, row in enumerate(rows):
        if not any(cell.strip() for cell in row):
            continue
        doc = {col: (row[i] if i < len(row) else "") for i, col in enumerate(cols)}
        for col in cols:
            value = doc[col]
            if col in BOOL_COLS:
                doc[col] = str(value).strip().lower() == "true"
            elif col in INT_COLS:
                doc[col] = int(value) if str(value).strip() else 0
            elif value == "":
                doc[col] = None
        doc["_row"] = offset + 2  # 1-based sheet row (headers on row 1)
        docs.append(doc)
    return docs


class SheetsStore(BaseStore):
    kind = "google-sheets"

    def __init__(self):
        info = service_account_info()
        self.spreadsheet_id = GOOGLE_SHEETS_ID
        self.service_account_email = info.get("client_email")
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=[SHEETS_SCOPE]
        )
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    def describe(self) -> str:
        return f"google-sheets://{self.spreadsheet_id}"

    def _call(self, request):
        try:
            return request.execute()
        except HttpError as exc:
            raise ApiError(502, "SHEETS_ERROR", self._friendly(exc)) from exc
        except Exception as exc:
            raise ApiError(502, "SHEETS_ERROR",
                           f"Google Sheets API call failed: {exc}") from exc

    @staticmethod
    def _friendly(exc: HttpError) -> str:
        status = exc.resp.status if exc.resp else 0
        if status == 403:
            return ("Google Sheets permission denied — share the spreadsheet with the "
                    "service-account email as Editor (see README → Google Sheets setup).")
        if status == 404:
            return "Spreadsheet not found — check GOOGLE_SHEETS_ID in backend/.env."
        if status == 401:
            return "Google rejected the service-account credentials — check GOOGLE_SERVICE_ACCOUNT_JSON."
        return f"Google Sheets API error (HTTP {status})."

    def ping(self) -> None:
        self._call(self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=f"{PROVIDERS_TAB}!A1:A1"))

    # ---- providers ----
    def list_providers(self) -> list[dict]:
        result = self._call(self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=f"{PROVIDERS_TAB}!A2:Z"))
        return _parse(result.get("values", []), PROVIDER_COLS)

    def get_provider(self, provider_id: str) -> dict | None:
        return next((p for p in self.list_providers() if p["id"] == provider_id), None)

    def insert_provider(self, provider: dict) -> dict:
        row = [_cell(provider.get(c)) for c in PROVIDER_COLS]
        self._call(self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, range=f"{PROVIDERS_TAB}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": [row]}))
        return provider

    def _rewrite_row(self, tab: str, cols: list[str], doc: dict) -> None:
        row = [_cell(doc.get(c)) for c in cols]
        self._call(self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id, range=f"{tab}!A{doc['_row']}",
            valueInputOption="RAW", body={"values": [row]}))

    def update_provider(self, provider_id: str, patch: dict) -> dict | None:
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        provider.update(patch)
        self._rewrite_row(PROVIDERS_TAB, PROVIDER_COLS, provider)
        return provider

    # ---- bookings ----
    def list_bookings(self, provider_id: str | None = None) -> list[dict]:
        result = self._call(self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=f"{BOOKINGS_TAB}!A2:Z"))
        bookings = _parse(result.get("values", []), BOOKING_COLS)
        if provider_id:
            bookings = [b for b in bookings if b["provider_id"] == provider_id]
        return bookings

    def get_booking(self, booking_id: str) -> dict | None:
        return next((b for b in self.list_bookings() if b["id"] == booking_id), None)

    def insert_booking(self, booking: dict) -> dict:
        row = [_cell(booking.get(c)) for c in BOOKING_COLS]
        self._call(self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, range=f"{BOOKINGS_TAB}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": [row]}))
        return booking

    def update_booking(self, booking_id: str, patch: dict) -> dict | None:
        booking = self.get_booking(booking_id)
        if not booking:
            return None
        booking.update(patch)
        self._rewrite_row(BOOKINGS_TAB, BOOKING_COLS, booking)
        return booking

    # ---- maintenance ----
    def clear_all(self) -> None:
        for tab in (PROVIDERS_TAB, BOOKINGS_TAB):
            result = self._call(self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=f"{tab}!A2:A10000"))
            count = len(result.get("values", []))
            if count == 0:
                continue
            meta = self._call(self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id, ranges=[tab],
                fields="sheets.properties.sheetId"))
            sheet_id = meta["sheets"][0]["properties"]["sheetId"]
            self._call(self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": [{"deleteDimension": {"range": {
                    "sheetId": sheet_id, "dimension": "ROWS",
                    "startIndex": 1, "endIndex": 1 + count}}}]},
            ))
