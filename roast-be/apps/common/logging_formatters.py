import json
import logging
from datetime import UTC, datetime

from .request_context import get_request_id

# Standard attributes every LogRecord has — anything else on the record was
# passed via `logger.info(..., extra={...})` and gets folded into the JSON
# output as a structured field. "message" is included even though it's not
# present until a Formatter.format() call sets it as a side effect (which
# can happen upstream of us, e.g. via Django's own default logger config
# propagating a record before it reaches our handler) — it's always
# redundant with the "message" field we compute ourselves below.
_STANDARD_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message"
}


class JSONFormatter(logging.Formatter):
    """
    Structured (JSON-lines) log formatter. Emits one JSON object per line
    with a stable set of base fields plus any caller-supplied `extra`
    fields.

    Policy: callers must never pass submission file bytes, extracted
    document text, AI prompts, or AI outputs containing private user
    content as the message or as an extra field — this formatter does
    not scrub content, it only structures whatever it's given.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_RECORD_ATTRS
        }
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, default=str)
