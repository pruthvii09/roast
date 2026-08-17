import io

import pytest
from django.core.exceptions import ImproperlyConfigured, SuspiciousFileOperation

from apps.common.storage import get_storage
from apps.common.storage.local import LocalFileSystemStorage

pytestmark = pytest.mark.django_db(transaction=False)


def test_save_open_delete_roundtrip(tmp_path):
    storage = LocalFileSystemStorage(root=tmp_path)
    key = "submissions/abc/file.pdf"

    returned_key = storage.save(key, io.BytesIO(b"hello world"))

    assert returned_key == key
    assert storage.exists(key) is True
    assert storage.size(key) == len(b"hello world")
    with storage.open(key) as f:
        assert f.read() == b"hello world"

    storage.delete(key)
    assert storage.exists(key) is False


def test_delete_is_idempotent(tmp_path):
    storage = LocalFileSystemStorage(root=tmp_path)
    storage.delete("submissions/does/not/exist.pdf")  # must not raise


def test_path_traversal_key_is_rejected(tmp_path):
    storage = LocalFileSystemStorage(root=tmp_path)
    with pytest.raises(SuspiciousFileOperation):
        storage.save("../../etc/passwd", io.BytesIO(b"evil"))


def test_get_storage_returns_local_backend(settings):
    settings.STORAGE_BACKEND = "local"
    storage = get_storage()
    assert isinstance(storage, LocalFileSystemStorage)


def test_get_storage_raises_on_unknown_backend(settings):
    settings.STORAGE_BACKEND = "s3-not-implemented-yet"
    with pytest.raises(ImproperlyConfigured):
        get_storage()
