import pypdf

from apps.extraction.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    UnsupportedContentTypeError,
)
from apps.extraction.tempfiles import materialize_asset_to_tempfile

from .base import ProcessingResult, SubmissionProcessor


def _parse_pdf(tmp) -> str:
    try:
        reader = pypdf.PdfReader(tmp)
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise CorruptedDocumentError(f"Could not parse PDF: {exc}") from exc
    text = "\n\n".join(page for page in pages if page.strip())
    if not text.strip():
        raise EmptyDocumentError(
            "Could not extract any text from the PDF (it may be scanned/image-only)."
        )
    return text


# Keyed by the asset's sniffed content type. Adding DOCX/image support
# later is one new parser function + one new entry here — no changes
# anywhere that calls ResumeProcessor or get_processor().
_FORMAT_PARSERS = {
    "application/pdf": _parse_pdf,
}


class ResumeProcessor(SubmissionProcessor):
    processor_name = "resume"

    def process(self, submission) -> ProcessingResult:
        asset = submission.assets.first()
        if asset is None:
            raise UnsupportedContentTypeError("Resume submission has no uploaded file.")

        parser = _FORMAT_PARSERS.get(asset.content_type)
        if parser is None:
            raise UnsupportedContentTypeError(
                f"No parser available yet for content type {asset.content_type!r}."
            )

        with materialize_asset_to_tempfile(asset, suffix=".pdf") as tmp:
            text = parser(tmp)

        return ProcessingResult(text=text)
