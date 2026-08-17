import uuid

from .request_context import VALID_REQUEST_ID, reset_request_id, set_request_id


class RequestIDMiddleware:
    """
    Generates (or accepts, if the client already supplied a plausible
    one) a request ID for correlating a client's bug report with the
    matching server-side log lines. Makes it available two ways:
    `request.request_id` (read directly by
    apps.common.exception_handler for the error envelope) and via a
    ContextVar (read automatically by
    apps.common.logging_formatters.JSONFormatter — see
    apps.common.request_context). Echoed back as the X-Request-ID
    response header.

    Placed early in MIDDLEWARE (right after SecurityMiddleware) so the
    id is available for the whole request lifecycle, including
    exception handling.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_supplied = request.headers.get("X-Request-ID", "")
        request_id = (
            client_supplied if VALID_REQUEST_ID.match(client_supplied) else str(uuid.uuid4())
        )
        request.request_id = request_id
        token = set_request_id(request_id)
        try:
            response = self.get_response(request)
        finally:
            reset_request_id(token)
        response["X-Request-ID"] = request_id
        return response
