"""Sahaay — local services platform backend (Flask).

create_app() builds the Flask application: CORS, JSON error handlers, the /api
blueprint and the active data store (Google Sheets when configured, SQLite
fallback for offline demos).
"""
import logging

from flask import Flask
from flask_cors import CORS

from sahaay.config import CORS_ORIGINS
from sahaay.errors import register_error_handlers


def _serve_frontend_build(app: Flask) -> None:
    """Offline/presentation mode: serve the built React app (frontend/dist) from Flask.

    With a build present, `python server.py` alone serves the whole website at
    http://localhost:8001 — no Node.js needed. /api routes are unaffected.
    """
    from pathlib import Path

    from flask import abort, send_from_directory

    dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if not (dist / "index.html").exists():
        return

    @app.get("/")
    @app.get("/<path:path>")
    def spa(path: str = ""):
        if path.startswith("api/"):
            abort(404)
        if path and (dist / path).is_file():
            return send_from_directory(dist, path)
        return send_from_directory(dist, "index.html")  # client-side routes


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False

    CORS(
        app,
        origins=CORS_ORIGINS,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    register_error_handlers(app)

    from sahaay.routes import api_bp
    from sahaay.storage import get_store

    app.register_blueprint(api_bp)
    _serve_frontend_build(app)

    store = get_store()
    app.logger.setLevel(logging.INFO)
    app.logger.info("Sahaay active store: %s", store.describe())
    return app
