import pytest

from apps.common.storage import get_storage
from apps.submissions.models import Submission, SubmissionAsset
from apps.submissions.tests.factories import SubmissionFactory

pytestmark = pytest.mark.django_db


def test_delete_removes_file_and_hides_submission(authenticated_client, user, valid_resume_file):
    create_response = authenticated_client.post(
        "/api/v1/submissions/",
        {"submission_type": "resume", "file": valid_resume_file},
        format="multipart",
    )
    submission_id = create_response.json()["data"]["id"]
    asset_id = create_response.json()["data"]["assets"][0]["id"]
    storage_key = SubmissionAsset.objects.get(pk=asset_id).storage_key

    delete_response = authenticated_client.delete(f"/api/v1/submissions/{submission_id}/")
    assert delete_response.status_code == 204

    assert get_storage().exists(storage_key) is False
    assert not SubmissionAsset.objects.filter(pk=asset_id).exists()
    assert not Submission.objects.filter(pk=submission_id).exists()

    get_response = authenticated_client.get(f"/api/v1/submissions/{submission_id}/")
    assert get_response.status_code == 404

    list_response = authenticated_client.get("/api/v1/submissions/")
    assert list_response.json()["meta"]["count"] == 0


def test_delete_requires_authentication(api_client, user):
    submission = SubmissionFactory(owner=user)
    response = api_client.delete(f"/api/v1/submissions/{submission.id}/")
    assert response.status_code == 401


def test_cannot_delete_other_users_submission(authenticated_client, user_factory):
    owner = user_factory(email="owner2@example.com")
    submission = SubmissionFactory(owner=owner)

    response = authenticated_client.delete(f"/api/v1/submissions/{submission.id}/")

    assert response.status_code == 404
    assert Submission.objects.filter(pk=submission.pk).exists()
