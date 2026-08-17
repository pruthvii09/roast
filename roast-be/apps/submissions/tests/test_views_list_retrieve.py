import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.submissions.models import SubmissionType
from apps.submissions.tests.factories import SubmissionFactory

pytestmark = pytest.mark.django_db


def _client_for(api_client_cls, user):
    client = api_client_cls()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class TestList:
    def test_list_is_owner_scoped(self, authenticated_client, user, user_factory):
        SubmissionFactory(owner=user)
        other_user = user_factory(email="other@example.com")
        SubmissionFactory(owner=other_user)

        response = authenticated_client.get("/api/v1/submissions/")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["count"] == 1

    def test_filter_by_submission_type(self, authenticated_client, user):
        SubmissionFactory(owner=user, submission_type=SubmissionType.WEBSITE)
        SubmissionFactory(
            owner=user, submission_type=SubmissionType.GITHUB, source_url="https://github.com/x"
        )

        response = authenticated_client.get("/api/v1/submissions/?submission_type=github")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["count"] == 1
        assert body["data"][0]["submission_type"] == "github"

    def test_list_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/submissions/")
        assert response.status_code == 401


class TestRetrieve:
    def test_owner_can_retrieve(self, authenticated_client, user):
        submission = SubmissionFactory(owner=user)
        response = authenticated_client.get(f"/api/v1/submissions/{submission.id}/")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == str(submission.id)

    def test_other_user_gets_404_not_403(self, api_client, user_factory):
        owner = user_factory(email="owner@example.com")
        submission = SubmissionFactory(owner=owner)
        other_user = user_factory(email="intruder@example.com")
        client = _client_for(type(api_client), other_user)

        response = client.get(f"/api/v1/submissions/{submission.id}/")

        assert response.status_code == 404

    def test_soft_deleted_submission_returns_404(self, authenticated_client, user):
        submission = SubmissionFactory(owner=user)
        submission.soft_delete()

        response = authenticated_client.get(f"/api/v1/submissions/{submission.id}/")

        assert response.status_code == 404
