import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from .conftest import MINIMAL_PDF_BYTES

pytestmark = pytest.mark.django_db


def _client_for(api_client_cls, user):
    client = api_client_cls()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


def _create_resume(client, valid_resume_file):
    response = client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": valid_resume_file},
        format="multipart",
    )
    data = response.json()["data"]
    return data["id"], data["assets"][0]["id"]


def test_owner_can_download_asset(authenticated_client, valid_resume_file):
    submission_id, asset_id = _create_resume(authenticated_client, valid_resume_file)

    response = authenticated_client.get(
        f"/api/v1/submissions/{submission_id}/assets/{asset_id}/download/"
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert b"".join(response.streaming_content) == MINIMAL_PDF_BYTES


def test_non_owner_gets_404(api_client, authenticated_client, user_factory, valid_resume_file):
    submission_id, asset_id = _create_resume(authenticated_client, valid_resume_file)
    intruder = user_factory(email="intruder2@example.com")
    intruder_client = _client_for(type(api_client), intruder)

    response = intruder_client.get(
        f"/api/v1/submissions/{submission_id}/assets/{asset_id}/download/"
    )

    assert response.status_code == 404


def test_unauthenticated_gets_401(api_client, authenticated_client, valid_resume_file):
    submission_id, asset_id = _create_resume(authenticated_client, valid_resume_file)

    response = api_client.get(f"/api/v1/submissions/{submission_id}/assets/{asset_id}/download/")

    assert response.status_code == 401


def test_download_of_deleted_submission_returns_404(authenticated_client, valid_resume_file):
    submission_id, asset_id = _create_resume(authenticated_client, valid_resume_file)
    authenticated_client.delete(f"/api/v1/submissions/{submission_id}/")

    response = authenticated_client.get(
        f"/api/v1/submissions/{submission_id}/assets/{asset_id}/download/"
    )

    assert response.status_code == 404
