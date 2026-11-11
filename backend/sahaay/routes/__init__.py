"""The /api blueprint — every REST route hangs off this router."""
from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/")
def api_index():
    return jsonify({
        "name": "Sahaay API",
        "version": "1.0.0",
        "description": "Local services platform — maids, electricians, carpenters and more.",
        "endpoints": [
            ["GET", "/api/health", "Store + service status"],
            ["GET", "/api/meta", "Categories, labels, server-anchored week strip"],
            ["POST", "/api/providers", "Provider registration (maid / tradesperson)"],
            ["GET", "/api/providers", "Search + filter providers"],
            ["GET", "/api/providers/{id}", "Public provider profile"],
            ["PATCH", "/api/providers/{id}", "Update availability / listing fields"],
            ["GET", "/api/providers/{id}/timetable", "Maid day timetable (?date=YYYY-MM-DD)"],
            ["POST", "/api/bookings", "Create booking request (auto-accepted)"],
            ["GET", "/api/bookings", "List bookings (?provider_id=)"],
            ["GET", "/api/bookings/{id}", "Booking detail (reveals provider phone)"],
            ["PATCH", "/api/bookings/{id}", "Update / cancel a booking"],
            ["POST", "/api/bookings/{id}/accept", "Accept a booking"],
            ["POST", "/api/bookings/{id}/reject", "Reject a booking"],
        ],
    })


# Importing the route modules registers their handlers on api_bp.
from sahaay.routes import bookings, meta, providers  # noqa: E402,F401
