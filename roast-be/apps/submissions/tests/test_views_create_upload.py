import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.submissions.models import Submission, SubmissionAsset

from .conftest import MINIMAL_PDF_BYTES

pytestmark = pytest.mark.django_db


def test_create_resume_via_multipart_upload(authenticated_client, valid_resume_file):
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": valid_resume_file},
        format="multipart",
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["submission_type"] == "resume"
    assert len(body["assets"]) == 1

    asset = SubmissionAsset.objects.get(pk=body["assets"][0]["id"])
    stored_path = settings.MEDIA_ROOT + "/" + asset.storage_key
    import os

    assert os.path.exists(stored_path)


def test_create_website_via_json(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "website", "source_url": "https://example.com/me"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["source_url"] == "https://example.com/me"
    assert body["assets"] == []


def test_malicious_client_filename_is_neutralized(authenticated_client):
    malicious_file = SimpleUploadedFile(
        "../../evil.pdf", MINIMAL_PDF_BYTES, content_type="application/pdf"
    )
    response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": malicious_file},
        format="multipart",
    )

    assert response.status_code == 201
    asset_id = response.json()["data"]["assets"][0]["id"]
    asset = SubmissionAsset.objects.get(pk=asset_id)

    # Django's multipart parser already reduces the client-supplied name to
    # its basename ("evil.pdf") before our code ever sees it; original_filename
    # is stored as inert metadata regardless and never influences where the
    # file actually lives on disk.
    assert asset.original_filename == "evil.pdf"
    assert ".." not in asset.storage_key
    assert asset.storage_key.startswith("submissions/")


def test_create_requires_authentication(api_client, valid_resume_file):
    response = api_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": valid_resume_file},
        format="multipart",
    )
    assert response.status_code == 401


def test_created_submission_is_owner_scoped(authenticated_client, user, valid_resume_file):
    authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": valid_resume_file},
        format="multipart",
    )
    assert Submission.objects.filter(owner=user).count() == 1
