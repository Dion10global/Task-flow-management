from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Return a consistent error envelope for all API errors."""
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": {
                "code": response.status_code,
                "message": _flatten_errors(response.data),
                "details": response.data,
            },
        }
        response.data = error_data
    else:
        logger.exception("Unhandled exception in view %s", context.get("view"))
        response = Response(
            {
                "success": False,
                "error": {
                    "code": 500,
                    "message": "An unexpected server error occurred.",
                    "details": {},
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _flatten_errors(data):
    """Produce a single human-readable error string from DRF error data."""
    if isinstance(data, list):
        return " ".join(str(e) for e in data)
    if isinstance(data, dict):
        messages = []
        for key, value in data.items():
            if key in ("code", "detail"):
                messages.append(str(value))
            elif isinstance(value, list):
                messages.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                messages.append(f"{key}: {value}")
        return " | ".join(messages)
    return str(data)
