import time
from typing import IO
from urllib.error import HTTPError
from urllib.request import urlopen

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import NotFound
from django.conf import settings

from .base import StorageBackend

_RESOURCE_TYPE = "raw"  # resumes are PDF/DOCX, never image/video
_DELIVERY_TYPE = "authenticated"  # private assets — never publicly deliverable
_SIGNED_URL_TTL_SECONDS = 60  # fetched immediately server-side; short window minimizes exposure


class CloudinaryStorage(StorageBackend):
    """
    Cloudinary-backed storage using private "authenticated" raw assets.
    Every SDK call passes resource_type/type identically — Cloudinary
    namespaces a resource by the (public_id, resource_type, type) triple,
    not by public_id alone, so a mismatch on any one of these on a later
    call looks exactly like "not found" even though the asset exists.
    """

    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    def save(self, key: str, file_obj: IO[bytes]) -> str:
        # `key` (from generate_storage_key) has a trailing extension like
        # ".pdf" — stripped here before use as public_id. Empirically
        # confirmed: a public_id ending in a recognized format extension
        # (.pdf/.doc/.docx) makes cloudinary.utils.cloudinary_url's
        # sign_url signature not match what Cloudinary recomputes
        # server-side, so every authenticated fetch 401s — a non-format
        # suffix (or no suffix) signs correctly. The extension isn't
        # needed downstream anyway: FileResponse's filename/content_type
        # come from SubmissionAsset.original_filename/content_type, never
        # from the storage key.
        public_id = key.rsplit(".", 1)[0] if "." in key else key
        result = cloudinary.uploader.upload(
            file_obj,
            public_id=public_id,
            resource_type=_RESOURCE_TYPE,
            type=_DELIVERY_TYPE,
            overwrite=True,
            unique_filename=False,
            use_filename=False,
        )
        # Persist whatever Cloudinary actually stored it under, not what
        # was requested — cheap insurance against any SDK/account-level
        # public_id normalization silently diverging from `public_id`.
        return result["public_id"]

    def open(self, key: str) -> IO[bytes]:
        url, _ = cloudinary.utils.cloudinary_url(
            key,
            resource_type=_RESOURCE_TYPE,
            type=_DELIVERY_TYPE,
            sign_url=True,
            expires_at=int(time.time()) + _SIGNED_URL_TTL_SECONDS,
        )
        try:
            return urlopen(url, timeout=settings.CLOUDINARY_HTTP_TIMEOUT_SECONDS)
        except HTTPError as exc:
            if exc.code in (401, 403, 404):
                raise FileNotFoundError(key) from exc
            raise

    def delete(self, key: str) -> None:
        result = cloudinary.uploader.destroy(
            key, resource_type=_RESOURCE_TYPE, type=_DELIVERY_TYPE, invalidate=True
        )
        # {"result": "not found"} is Cloudinary's normal response for an
        # already-absent asset — treat it like local's unlink(missing_ok=True).
        if result.get("result") not in ("ok", "not found"):
            raise RuntimeError(f"Cloudinary destroy failed for {key!r}: {result}")

    def exists(self, key: str) -> bool:
        try:
            cloudinary.api.resource(key, resource_type=_RESOURCE_TYPE, type=_DELIVERY_TYPE)
            return True
        except NotFound:
            return False

    def size(self, key: str) -> int:
        return cloudinary.api.resource(key, resource_type=_RESOURCE_TYPE, type=_DELIVERY_TYPE)[
            "bytes"
        ]

    def generate_upload_url(self, key: str, content_type: str, expires_in: int = 900) -> str | None:
        # No call sites use this today (see base.py's docstring) — keep
        # the same "unsupported, fall back to synchronous upload"
        # contract the local backend uses rather than building an unused
        # presigned-upload path.
        return None
