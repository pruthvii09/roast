import io
from unittest.mock import MagicMock, patch

import pytest
from cloudinary.exceptions import NotFound

from apps.common.storage import get_storage
from apps.common.storage.cloudinary import CloudinaryStorage

pytestmark = pytest.mark.django_db(transaction=False)


class _NamedBytesIO(io.BytesIO):
    """Stands in for Django's UploadedFile, which always carries a `.name`."""

    name = "resume.pdf"


@pytest.fixture(autouse=True)
def cloudinary_settings(settings):
    settings.CLOUDINARY_CLOUD_NAME = "test-cloud"
    settings.CLOUDINARY_API_KEY = "test-key"
    settings.CLOUDINARY_API_SECRET = "test-secret"
    settings.CLOUDINARY_HTTP_TIMEOUT_SECONDS = 10.0


def test_save_strips_extension_and_returns_public_id_from_response():
    storage = CloudinaryStorage()
    with patch("apps.common.storage.cloudinary.cloudinary.uploader.upload") as upload:
        upload.return_value = {"public_id": "submissions/abc/file", "bytes": 11}

        returned_key = storage.save("submissions/abc/file.pdf", _NamedBytesIO(b"hello world"))

    assert returned_key == "submissions/abc/file"
    _, kwargs = upload.call_args
    # The extension is deliberately stripped before use as public_id — a
    # trailing recognized-format extension breaks signed authenticated
    # URL fetches (empirically confirmed against the real Cloudinary API,
    # not just an in-code assumption).
    assert kwargs["public_id"] == "submissions/abc/file"
    assert kwargs["resource_type"] == "raw"
    assert kwargs["type"] == "authenticated"


def test_save_uploads_an_unnamed_copy_to_avoid_cloudinary_reappending_extension():
    # Cloudinary auto-detects format from the source object's `.name`
    # (independent of use_filename=False) and re-appends it server-side —
    # confirmed against the real API. `save()` must upload a plain,
    # unnamed BytesIO so Cloudinary has nothing to detect from.
    storage = CloudinaryStorage()
    with patch("apps.common.storage.cloudinary.cloudinary.uploader.upload") as upload:
        upload.return_value = {"public_id": "submissions/abc/file", "bytes": 11}

        storage.save("submissions/abc/file.pdf", _NamedBytesIO(b"hello world"))

    args, _ = upload.call_args
    uploaded_obj = args[0]
    assert not hasattr(uploaded_obj, "name")
    assert uploaded_obj.getvalue() == b"hello world"


def test_open_builds_signed_url_and_returns_response():
    storage = CloudinaryStorage()
    fake_response = MagicMock()
    with (
        patch("apps.common.storage.cloudinary.cloudinary.utils.cloudinary_url") as cloudinary_url,
        patch("apps.common.storage.cloudinary.urlopen") as urlopen,
    ):
        cloudinary_url.return_value = ("https://signed.example/file.pdf", {})
        urlopen.return_value = fake_response

        result = storage.open("submissions/abc/file.pdf")

    assert result is fake_response
    _, url_kwargs = cloudinary_url.call_args
    assert url_kwargs["resource_type"] == "raw"
    assert url_kwargs["type"] == "authenticated"
    assert url_kwargs["sign_url"] is True
    urlopen.assert_called_once_with("https://signed.example/file.pdf", timeout=10.0)


def test_open_raises_file_not_found_on_404():
    from urllib.error import HTTPError

    storage = CloudinaryStorage()
    with (
        patch("apps.common.storage.cloudinary.cloudinary.utils.cloudinary_url") as cloudinary_url,
        patch("apps.common.storage.cloudinary.urlopen") as urlopen,
    ):
        cloudinary_url.return_value = ("https://signed.example/missing.pdf", {})
        urlopen.side_effect = HTTPError(
            "https://signed.example/missing.pdf", 404, "Not Found", {}, None
        )

        with pytest.raises(FileNotFoundError):
            storage.open("submissions/missing.pdf")


def test_delete_treats_ok_and_not_found_as_success():
    storage = CloudinaryStorage()
    with patch("apps.common.storage.cloudinary.cloudinary.uploader.destroy") as destroy:
        destroy.return_value = {"result": "ok"}
        storage.delete("submissions/abc/file.pdf")  # must not raise

        destroy.return_value = {"result": "not found"}
        storage.delete("submissions/does/not/exist.pdf")  # must not raise


def test_delete_raises_on_unexpected_result():
    storage = CloudinaryStorage()
    with patch("apps.common.storage.cloudinary.cloudinary.uploader.destroy") as destroy:
        destroy.return_value = {"result": "error"}
        with pytest.raises(RuntimeError):
            storage.delete("submissions/abc/file.pdf")


def test_exists_true_and_false():
    storage = CloudinaryStorage()
    with patch("apps.common.storage.cloudinary.cloudinary.api.resource") as resource:
        resource.return_value = {"bytes": 11}
        assert storage.exists("submissions/abc/file.pdf") is True

        resource.side_effect = NotFound("not found")
        assert storage.exists("submissions/missing.pdf") is False


def test_size_reads_bytes_field():
    storage = CloudinaryStorage()
    with patch("apps.common.storage.cloudinary.cloudinary.api.resource") as resource:
        resource.return_value = {"bytes": 42}
        assert storage.size("submissions/abc/file.pdf") == 42


def test_generate_upload_url_returns_none():
    storage = CloudinaryStorage()
    assert storage.generate_upload_url("submissions/abc/file.pdf", "application/pdf") is None


def test_get_storage_returns_cloudinary_backend(settings):
    settings.STORAGE_BACKEND = "cloudinary"
    storage = get_storage()
    assert isinstance(storage, CloudinaryStorage)
