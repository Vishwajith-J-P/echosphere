from __future__ import annotations

from uuid import uuid4
import re
from werkzeug.exceptions import HTTPException

from flask import Flask, jsonify, request


class ApiError(RuntimeError):
    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def register_error_handlers(app: Flask) -> None:
    @app.before_request
    def attach_correlation_id() -> None:
        supplied = request.headers.get("X-Correlation-ID", "")
        safe = supplied if re.fullmatch(r'[A-Za-z0-9_-]{1,64}', supplied) else ''
        request.environ["echosphere.correlation_id"] = safe or str(uuid4())

    @app.after_request
    def include_correlation_id(response):
        response.headers["X-Correlation-ID"] = request.environ[
            "echosphere.correlation_id"
        ]
        response.headers["Cache-Control"] = "no-store"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return (
            jsonify(
                error={
                    "code": error.code,
                    "message": error.message,
                    "correlation_id": request.environ["echosphere.correlation_id"],
                }
            ),
            error.status,
        )

    @app.errorhandler(404)
    def handle_not_found(_error):
        return (
            jsonify(
                error={
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "correlation_id": request.environ["echosphere.correlation_id"],
                }
            ),
            404,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        status = error.code if isinstance(error, HTTPException) else 500
        code = 'VALIDATION_ERROR' if status in {400, 413, 415} else 'INTERNAL_ERROR'
        # Do not log exception text: provider errors can include credentials or transcripts.
        app.logger.warning('request_failed status=%s correlation=%s', status, request.environ.get('echosphere.correlation_id'))
        return jsonify(error={'code': code, 'message': 'The request could not be completed.',
            'correlation_id': request.environ.get('echosphere.correlation_id')}), status
