from pathlib import Path
from typing import IO

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation

from .base import StorageBackend


class LocalFileSystemStorage(StorageBackend):
    """
    Filesystem-backed storage rooted at settings.MEDIA_ROOT. Keys are
    always server-generated opaque paths (see
    apps.common.validation.keys.generate_storage_key) — never derived
    from client input. The containment check in `_resolve` is
    defense-in-depth against a future bug that accidentally passes a
    client-controlled value in as a key.
    """

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or settings.MEDIA_ROOT).resolve()

    def _resolve(self, key: str) -> Path:
        full = (self.root / key).resolve()
        if full != self.root and self.root not in full.parents:
            raise SuspiciousFileOperation(f"Resolved path escapes storage root: {key!r}")
        return full

    def save(self, key: str, file_obj: IO[bytes]) -> str:
        full = self._resolve(key)
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "wb") as dest:
            for chunk in iter(lambda: file_obj.read(64 * 1024), b""):
                dest.write(chunk)
        return key

    def open(self, key: str) -> IO[bytes]:
        return open(self._resolve(key), "rb")

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def size(self, key: str) -> int:
        return self._resolve(key).stat().st_size

    def generate_upload_url(self, key: str, content_type: str, expires_in: int = 900) -> str | None:
        # The local filesystem has no concept of a presigned upload URL —
        # callers fall back to the synchronous multipart upload path.
        return None
