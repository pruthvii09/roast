import re
from contextvars import ContextVar, Token

#: Client-supplied X-Request-ID is only trusted if it matches this shape
#: (alphanumeric/hyphen, length-capped) — anything else is replaced with a
#: freshly generated id, so a client can't inject arbitrary/huge strings
#: into structured logs via this header. See apps.common.middleware.
VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,100}$")

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> Token:
    return _request_id_ctx.set(request_id)


def reset_request_id(token: Token) -> None:
    _request_id_ctx.reset(token)


def get_request_id() -> str | None:
    """
    Read by apps.common.logging_formatters.JSONFormatter so ordinary
    `logger.*` calls automatically get a request_id field without every
    call site needing to thread one through manually. None outside an
    HTTP request handled by apps.common.middleware.RequestIDMiddleware
    (e.g. a Celery task, a management command).
    """
    return _request_id_ctx.get()
