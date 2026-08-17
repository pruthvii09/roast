import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.exceptions import FileValidationError
from apps.common.validation.files import (
    sniff_content_type,
    validate_extension,
    validate_file_size,
    validate_file_type,
)
from apps.common.validation.keys import generate_storage_key

MINIMAL_PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def _uploaded(name, content, content_type):
    return SimpleUploadedFile(name, content, content_type=content_type)


class TestSniffContentType:
    def test_detects_real_pdf(self):
        f = _uploaded("resume.pdf", MINIMAL_PDF_BYTES, "application/pdf")
        assert sniff_content_type(f) == "application/pdf"

    def test_ignores_client_supplied_content_type_for_spoofed_file(self):
        # A plain text file renamed to .pdf, claiming to be a PDF via
        # Content-Type — sniffing must see through the spoof.
        f = _uploaded("resume.pdf", b"just plain text, not a pdf", "application/pdf")
        assert sniff_content_type(f) != "application/pdf"

    def test_resets_position_after_sniffing(self):
        f = _uploaded("resume.pdf", MINIMAL_PDF_BYTES, "application/pdf")
        sniff_content_type(f)
        assert f.read() == MINIMAL_PDF_BYTES


class TestValidateFileSize:
    def test_exactly_at_limit_passes(self):
        f = _uploaded("resume.pdf", b"x" * 100, "application/pdf")
        validate_file_size(f, max_bytes=100)  # must not raise

    def test_over_limit_raises(self):
        f = _uploaded("resume.pdf", b"x" * 101, "application/pdf")
        with pytest.raises(FileValidationError):
            validate_file_size(f, max_bytes=100)

    def test_empty_file_raises(self):
        f = _uploaded("resume.pdf", b"", "application/pdf")
        with pytest.raises(FileValidationError):
            validate_file_size(f, max_bytes=100)


class TestValidateExtension:
    def test_allowed_extension_passes(self):
        assert validate_extension("resume.pdf", [".pdf", ".docx"]) == ".pdf"

    def test_disallowed_extension_raises(self):
        with pytest.raises(FileValidationError):
            validate_extension("resume.exe", [".pdf", ".docx"])

    def test_is_case_insensitive(self):
        assert validate_extension("resume.PDF", [".pdf"]) == ".pdf"


class TestValidateFileType:
    def test_real_pdf_with_correct_extension_passes(self):
        f = _uploaded("resume.pdf", MINIMAL_PDF_BYTES, "application/pdf")
        content_type, ext = validate_file_type(
            f,
            allowed_content_types=["application/pdf"],
            allowed_extensions=[".pdf"],
            filename="resume.pdf",
        )
        assert content_type == "application/pdf"
        assert ext == ".pdf"

    def test_spoofed_extension_is_rejected(self):
        # Text content, .pdf extension, claims application/pdf via header —
        # must be rejected because the *sniffed* type isn't application/pdf.
        f = _uploaded("resume.pdf", b"not actually a pdf", "application/pdf")
        with pytest.raises(FileValidationError):
            validate_file_type(
                f,
                allowed_content_types=["application/pdf"],
                allowed_extensions=[".pdf"],
                filename="resume.pdf",
            )

    def test_disallowed_extension_is_rejected_before_sniffing(self):
        f = _uploaded("resume.exe", MINIMAL_PDF_BYTES, "application/pdf")
        with pytest.raises(FileValidationError):
            validate_file_type(
                f,
                allowed_content_types=["application/pdf"],
                allowed_extensions=[".pdf"],
                filename="resume.exe",
            )


class TestGenerateStorageKey:
    def test_produces_unique_keys(self):
        keys = {generate_storage_key(namespace="submissions", extension=".pdf") for _ in range(50)}
        assert len(keys) == 50

    def test_key_has_no_path_traversal_components(self):
        key = generate_storage_key(namespace="submissions", extension=".pdf")
        assert ".." not in key
        assert key.startswith("submissions/")
        assert key.endswith(".pdf")
