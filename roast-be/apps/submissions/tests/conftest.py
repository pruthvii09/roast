import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

MINIMAL_PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def valid_resume_file():
    return SimpleUploadedFile("resume.pdf", MINIMAL_PDF_BYTES, content_type="application/pdf")


@pytest.fixture
def oversized_resume_file(settings):
    settings.MAX_UPLOAD_SIZE_BYTES = 10
    return SimpleUploadedFile(
        "resume.pdf", MINIMAL_PDF_BYTES + b"0" * 100, content_type="application/pdf"
    )


@pytest.fixture
def spoofed_resume_file():
    # Plain text renamed to .pdf, lying about its Content-Type — must be
    # rejected once real content sniffing runs.
    return SimpleUploadedFile(
        "resume.pdf", b"just plain text, not a real pdf", content_type="application/pdf"
    )
