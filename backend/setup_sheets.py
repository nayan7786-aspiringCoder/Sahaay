"""Create the required Google Sheets tabs + column headers.

Run once after sharing your spreadsheet with the service account:
    cd backend && python setup_sheets.py

Creates (if missing):
  Tab "Providers"  with the 16 header columns
  Tab "Bookings"   with the 12 header columns
and freezes row 1 on both.
"""
import sys

from sahaay import config
from sahaay.sheets_store import BOOKINGS_TAB, BOOKING_COLS, PROVIDERS_TAB, PROVIDER_COLS


def main() -> None:
    if not config.sheets_configured():
        print("Google Sheets is not configured (GOOGLE_SHEETS_ID / GOOGLE_SERVICE_ACCOUNT_JSON).")
        print("The app runs fine without it on the local SQLite store — nothing to set up.")
        sys.exit(0)

    from sahaay.sheets_store import SheetsStore

    store = SheetsStore()
    print(f"Spreadsheet: {store.spreadsheet_id}")
    print(f"Service account: {store.service_account_email}")
    print("→ Make sure this account has EDITOR access to the spreadsheet (Share → add email).\n")

    meta = store._call(store.service.spreadsheets().get(
        spreadsheetId=store.spreadsheet_id, fields="sheets.properties.title,sheets.properties.sheetId"))
    sheets = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    requests = []
    for tab, cols in ((PROVIDERS_TAB, PROVIDER_COLS), (BOOKINGS_TAB, BOOKING_COLS)):
        if tab not in sheets:
            print(f"Creating tab “{tab}”…")
            requests.append({"addSheet": {"properties": {"title": tab}}})
    if requests:
        result = store._call(store.service.spreadsheets().batchUpdate(
            spreadsheetId=store.spreadsheet_id, body={"requests": requests}))
        for i, reply in enumerate(result.get("replies", [])):
            if "addSheet" in reply:
                sheets[requests[i]["addSheet"]["properties"]["title"]] = \
                    reply["addSheet"]["properties"]["sheetId"]

    for tab, cols in ((PROVIDERS_TAB, PROVIDER_COLS), (BOOKINGS_TAB, BOOKING_COLS)):
        store._call(store.service.spreadsheets().values().update(
            spreadsheetId=store.spreadsheet_id, range=f"{tab}!A1",
            valueInputOption="RAW", body={"values": [cols]}))
        store._call(store.service.spreadsheets().batchUpdate(
            spreadsheetId=store.spreadsheet_id,
            body={"requests": [{"updateSheetProperties": {
                "properties": {"sheetId": sheets[tab], "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }}]}))
        print(f"“{tab}” ready: {len(cols)} columns, header row frozen.")

    print("\nDone. Start (or seed) the app:  cd backend && python seed.py")


if __name__ == "__main__":
    main()
