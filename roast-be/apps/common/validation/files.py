import os
from typing import IO

import magic

from apps.common.exceptions import FileValidationError

_SNIFF_BYTES = 8192


def sniff_content_type(file_obj: IO[bytes]) -> str:
    """
    Determines the *actual* MIME type of a file by inspecting its content
    (via libmagic), ignoring any client-supplied Content-Type header or
    filename extension entirely. Resets the file position to 0 afterward
    so the caller can still read/save the full file.
    """
    try:
        file_obj.seek(0)
        header = file_obj.read(_SNIFF_BYTES)
        file_obj.seek(0)
    except OSError as exc:
        raise FileValidationError("Could not read uploaded file.") from exc
    return magic.from_buffer(header, mime=True)


def validate_file_size(file_obj, max_bytes: int) -> None:
    size = getattr(file_obj, "size", None)
    if size is None:
        raise FileValidationError("Uploaded file has no determinable size.")
    if size == 0:
        raise FileValidationError("Uploaded file is empty.")
    if size > max_bytes:
        raise FileValidationError(
            f"Uploaded file exceeds the maximum allowed size of {max_bytes} bytes."
        )


def validate_extension(filename: str, allowed_extensions: list[str]) -> str:
    """
    Extracts and lowercases the extension from the *original* filename
    purely as a plausibility check and to pick a display/storage
    extension — this value is NEVER used to build a storage path (see
    apps.common.validation.keys.generate_storage_key).
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in allowed_extensions:
        raise FileValidationError(
            f"File extension {ext!r} is not allowed. Allowed: {allowed_extensions}."
        )
    return ext


def validate_file_type(
    file_obj, allowed_content_types: list[str], allowed_extensions: list[str], filename: str
) -> tuple[str, str]:
    """
    Composes sniff_content_type + validate_extension. Raises
    FileValidationError if the sniffed real MIME type is not in
    allowed_content_types, catching spoofed-extension attacks (e.g. a
    text file renamed to .pdf). Returns (content_type, extension).
    """
    extension = validate_extension(filename, allowed_extensions)
    content_type = sniff_content_type(file_obj)
    if content_type not in allowed_content_types:
        raise FileValidationError(f"Detected file content type {content_type!r} is not allowed.")
    return content_type, extension
