import tempfile
from contextlib import contextmanager
from typing import IO

from apps.common.storage import get_storage

_CHUNK_SIZE = 64 * 1024


@contextmanager
def materialize_asset_to_tempfile(asset, *, suffix: str = "") -> IO[bytes]:
    """
    Streams a SubmissionAsset's bytes from storage into a securely
    created, auto-deleted local temp file, and yields it seeked to 0.

    Every file-based extractor should read through this rather than
    calling get_storage().open() directly: it's what keeps extraction
    storage-backend-agnostic (a future non-local StorageBackend has no
    obligation to hand back a real local file) and guarantees the bytes
    never linger on disk past this context — NamedTemporaryFile creates
    the file with owner-only (0600) permissions and unlinks it on exit
    even if extraction raises.
    """
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        with get_storage().open(asset.storage_key) as src:
            for chunk in iter(lambda: src.read(_CHUNK_SIZE), b""):
                tmp.write(chunk)
        tmp.flush()
        tmp.seek(0)
        yield tmp
