class ExtractionError(Exception):
    """
    Base class for any reason a submission's source material could not be
    turned into usable text. Callers (apps.extraction.services) catch this
    class, never a bare Exception, so an unexpected bug in an extractor
    surfaces as a real 500/unexpected-error path instead of silently
    being recorded as a normal extraction failure.
    """


class UnsupportedContentTypeError(ExtractionError):
    """No processor is registered for this asset's content type / submission type yet."""


class CorruptedDocumentError(ExtractionError):
    """The document could not be parsed (malformed/corrupt file)."""


class EmptyDocumentError(ExtractionError):
    """Processing succeeded but produced no usable extractable text."""


class ExtractionTimeoutError(ExtractionError):
    """Extraction did not complete within the allotted time."""


class InvalidSourceURLError(ExtractionError):
    """
    submission.source_url is missing, malformed, unsafe (fails the SSRF
    guard), or doesn't match the shape a processor expects (e.g. not a
    github.com URL, or no owner/repo identifiable in the path).
    """


class RemoteFetchError(ExtractionError):
    """A remote HTTP request needed for processing failed (network, timeout, non-2xx status)."""
