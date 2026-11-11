"""Configuration — everything comes from environment variables.

backend/.env is loaded via python-dotenv so a local checkout works without
exporting anything. Credentials never live in source code.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent  # backend/

load_dotenv(ROOT_DIR / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


# auto → use Google Sheets when both credentials are present, else SQLite (offline)
STORE_MODE = _env("STORE_MODE", "auto")
GOOGLE_SHEETS_ID = _env("GOOGLE_SHEETS_ID")
# Raw service-account JSON, or a path to the JSON file (relative paths resolve against backend/)
GOOGLE_SERVICE_ACCOUNT_JSON = _env("GOOGLE_SERVICE_ACCOUNT_JSON")

DATA_DIR = Path(_env("DATA_DIR", str(ROOT_DIR / "data")))
SQLITE_PATH = Path(_env("SQLITE_PATH", str(DATA_DIR / "sahaay.db")))

CORS_ORIGINS = [o.strip() for o in _env("CORS_ORIGINS", "*").split(",") if o.strip()]
APP_TIMEZONE = _env("APP_TIMEZONE", "Asia/Kolkata")

SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def sheets_configured() -> bool:
    return bool(GOOGLE_SHEETS_ID and GOOGLE_SERVICE_ACCOUNT_JSON)


def store_mode_resolved() -> str:
    if STORE_MODE in ("sheets", "sqlite"):
        return STORE_MODE
    return "sheets" if sheets_configured() else "sqlite"


def _parse_sa_json(text: str) -> dict:
    """Parse service-account JSON, repairing values trimmed by secret stores."""
    text = text.strip()
    try:
        info = json.loads(text)
    except json.JSONDecodeError:
        repaired = text
        if not repaired.startswith("{") and '"private_key"' in repaired:
            repaired = "{" + repaired
        if not repaired.endswith("}") and '"client_email"' in repaired:
            repaired = repaired + "}"
        try:
            info = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not valid service-account JSON"
            ) from exc
    if "client_email" not in info or "private_key" not in info:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON does not look like a service-account key")
    return info


def service_account_info() -> dict:
    """Load the service-account credentials. Accepts a raw JSON string or a file path."""
    raw = (GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
    if raw.startswith("{") or '"private_key"' in raw:
        return _parse_sa_json(raw)
    path = Path(raw.strip("\"'"))
    if not path.is_absolute():
        path = ROOT_DIR / path
    if not path.exists():
        raise RuntimeError(f"GOOGLE_SERVICE_ACCOUNT_JSON points to a missing file: {path}")
    return _parse_sa_json(path.read_text())
