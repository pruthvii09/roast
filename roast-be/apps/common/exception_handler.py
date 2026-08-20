import logging

from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

_ERROR_CODES = {
    drf_exceptions.ValidationError: "VALIDATION_ERROR",
    drf_exceptions.NotAuthenticated: "AUTHENTICATION_FAILED",
    drf_exceptions.AuthenticationFailed: "AUTHENTICATION_FAILED",
    drf_exceptions.PermissionDenied: "PERMISSION_DENIED",
    drf_exceptions.NotFound: "NOT_FOUND",
    drf_exceptions.MethodNotAllowed: "METHOD_NOT_ALLOWED",
    drf_exceptions.Throttled: "THROTTLED",
}


def _error_code_for(exc):
    # A generic extension point: any app can define its own distinctly-
    # coded exception (see apps.accounts.exceptions.EmailNotVerifiedError)
    # without apps.common ever needing to import from it. Checked before
    # the class-based table below since e.g. EmailNotVerifiedError IS an
    # AuthenticationFailed and would otherwise match that entry first.
    custom_code = getattr(exc, "api_error_code", None)
    if custom_code:
        return custom_code
    for exc_type, code in _ERROR_CODES.items():
        if isinstance(exc, exc_type):
            return code
    return "ERROR"


def _request_id_from(context) -> str | None:
    # Set by apps.common.middleware.RequestIDMiddleware; absent only for
    # requests that somehow never went through it (shouldn't happen in
    # practice — it's early in MIDDLEWARE — but this must never itself
    # raise while already handling an exception).
    request = context.get("request")
    return getattr(request, "request_id", None) if request is not None else None


def custom_exception_handler(exc, context):
    """
    Renders every DRF-raised error as:
        {"success": false, "error": {"code", "message", "details", "request_id"}}
    Unhandled exceptions never leak stack traces/DB details to the client —
    they're logged server-side (metadata only, never request bodies/file
    content) and returned as a generic 500 envelope. `request_id` lets a
    user hand support a traceable value without exposing anything about
    the failure itself.
    """
    request_id = _request_id_from(context)

    if (response := drf_exception_handler(exc, context)) is None:
        logger.exception("Unhandled exception in view %s", context.get("view"))
        return Response(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": None,
                    "request_id": request_id,
                },
            },
            status=500,
        )

    details = response.data
    message = details if isinstance(details, str) else "Request failed validation or processing."
    if isinstance(details, dict) and "detail" in details and len(details) == 1:
        message = details["detail"]

    response.data = {
        "success": False,
        "error": {
            "code": _error_code_for(exc),
            "message": str(message),
            "details": details,
            "request_id": request_id,
        },
    }
    return response
