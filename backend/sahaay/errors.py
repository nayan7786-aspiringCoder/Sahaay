"""Consistent JSON error responses.

Every error — raised or HTTP-level — keeps the same shape:
    {"error": {"code": "...", "message": "...", "details": [...]}}
"""


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: list | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []


def error_body(code: str, message: str, details: list | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


def register_error_handlers(app):
    from flask import jsonify
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify(error_body(err.code, err.message, err.details)), err.status

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        codes = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            413: "PAYLOAD_TOO_LARGE",
            415: "UNSUPPORTED_MEDIA_TYPE",
        }
        return (
            jsonify(error_body(codes.get(err.code, "HTTP_ERROR"), err.description or err.name)),
            err.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        app.logger.exception("unhandled error")
        return jsonify(error_body("INTERNAL_ERROR", "Something went wrong. Please try again.")), 500
