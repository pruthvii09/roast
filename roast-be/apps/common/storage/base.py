import abc
from typing import IO


class StorageBackend(abc.ABC):
    """
    Provider-agnostic file storage interface. All app code must go through
    get_storage() and this interface — never Django's default_storage or a
    raw open() call — so a future backend (e.g. S3-compatible, via
    django-storages) can be swapped in purely via settings/env config with
    zero call-site changes.
    """

    @abc.abstractmethod
    def save(self, key: str, file_obj: IO[bytes]) -> str:
        """Persist bytes at `key`. Returns the storage key actually used."""

    @abc.abstractmethod
    def open(self, key: str) -> IO[bytes]:
        """Return a readable, streamable file-like object for `key`."""

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Hard-delete the object at `key`. Idempotent: no-op if absent."""

    @abc.abstractmethod
    def exists(self, key: str) -> bool: ...

    @abc.abstractmethod
    def size(self, key: str) -> int: ...

    @abc.abstractmethod
    def generate_upload_url(self, key: str, content_type: str, expires_in: int = 900) -> str | None:
        """
        Returns a presigned URL the client can upload directly to,
        bypassing the app server entirely — supported by object-storage
        backends like S3/R2/GCS. Returns None for backends that don't
        support this (e.g. local filesystem); callers must treat None as
        "fall back to the synchronous multipart upload path", not as an
        error. This is the extension point that lets a future backend
        support direct-to-storage uploads without changing any call site
        that still uses `save()`.
        """
