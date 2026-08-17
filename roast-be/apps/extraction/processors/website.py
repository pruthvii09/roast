from html.parser import HTMLParser

from django.conf import settings

from apps.extraction.exceptions import EmptyDocumentError, InvalidSourceURLError
from apps.extraction.http import fetch_url, is_safe_public_url
from apps.extraction.text_utils import normalize_text

from .base import ProcessingResult, SubmissionProcessor

_USER_AGENT = "RoastAnythingBot/1.0"


class _VisibleTextExtractor(HTMLParser):
    """Strips <script>/<style> content and collapses the rest to plain text."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._chunks.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._chunks)


class WebsiteProcessor(SubmissionProcessor):
    """
    Fetches a public web page and extracts its visible text. Assumes
    the fetched resource is HTML/text and does not execute JavaScript —
    a JS-rendered single-page app will likely yield little or no text
    (documented limitation, not addressed this phase).
    """

    processor_name = "website"

    def process(self, submission) -> ProcessingResult:
        url = submission.source_url
        if not url or not is_safe_public_url(url):
            raise InvalidSourceURLError(
                "URL is missing, malformed, or not a safe public http(s) URL."
            )

        response = fetch_url(
            url,
            timeout=settings.EXTRACTION_HTTP_TIMEOUT_SECONDS,
            max_bytes=settings.EXTRACTION_HTTP_MAX_RESPONSE_BYTES,
            headers={"User-Agent": _USER_AGENT},
        )

        html = response.body.decode(response.encoding or "utf-8", errors="replace")
        parser = _VisibleTextExtractor()
        parser.feed(html)
        text = normalize_text(parser.get_text(), max_chars=settings.EXTRACTION_MAX_TEXT_CHARS)
        if not text:
            raise EmptyDocumentError("No visible text content found at this URL.")

        metadata = {
            "source_url": url,
            "content_type": response.content_type,
            "fetched_bytes": len(response.body),
        }
        return ProcessingResult(text=text, metadata=metadata)
