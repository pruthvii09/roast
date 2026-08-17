from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import StorageBackend
from .local import LocalFileSystemStorage

_BACKENDS = {
    "local": LocalFileSystemStorage,
}


def get_storage() -> StorageBackend:
    """
    Returns a StorageBackend instance for settings.STORAGE_BACKEND.
    Deliberately not cached as a module-level singleton: constructing a
    backend is cheap (just reads settings), and caching would risk
    returning a stale instance if MEDIA_ROOT/STORAGE_BACKEND changes
    between calls (e.g. in tests using pytest-django's `settings`
    fixture). Adding an S3-compatible backend later is: one new
    StorageBackend subclass + one new entry in _BACKENDS + an env var
    change — no call-site changes anywhere.
    """
    backend_name = settings.STORAGE_BACKEND
    try:
        backend_cls = _BACKENDS[backend_name]
    except KeyError:
        raise ImproperlyConfigured(f"Unknown STORAGE_BACKEND: {backend_name!r}") from None
    return backend_cls()
