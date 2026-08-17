import pytest

from apps.roasts.models import RoastStatus
from apps.roasts.tests.factories import RoastRunFactory
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


class TestShareLinkListCreateView:
    def test_create_returns_201_first_call(self, authenticated_client, user):
        roast = RoastRunFactory(submission__owner=user)

        response = authenticated_client.post(f"/api/v1/share/roasts/{roast.id}/links/")

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_active"] is True
        assert data["view_count"] == 0
        assert data["token"]
        assert data["share_url"].endswith(f"/r/{data['token']}")

    def test_create_returns_200_on_repeat(self, authenticated_client, user):
        roast = RoastRunFactory(submission__owner=user)

        first = authenticated_client.post(f"/api/v1/share/roasts/{roast.id}/links/")
        second = authenticated_client.post(f"/api/v1/share/roasts/{roast.id}/links/")

        assert first.status_code == 201
        assert second.status_code == 200
        assert first.json()["data"]["id"] == second.json()["data"]["id"]

    def test_create_rejects_non_completed_roast(self, authenticated_client, user):
        roast = RoastRunFactory(submission__owner=user, status=RoastStatus.PROCESSING)

        response = authenticated_client.post(f"/api/v1/share/roasts/{roast.id}/links/")

        assert response.status_code == 400

    def test_create_404s_for_other_users_roast(self, authenticated_client, user_factory):
        other = user_factory(email="share-owner2@example.com")
        roast = RoastRunFactory(submission__owner=other)

        response = authenticated_client.post(f"/api/v1/share/roasts/{roast.id}/links/")

        assert response.status_code == 404

    def test_create_requires_authentication(self, api_client, user):
        roast = RoastRunFactory(submission__owner=user)

        response = api_client.post(f"/api/v1/share/roasts/{roast.id}/links/")

        assert response.status_code == 401

    def test_list_returns_link_history(self, authenticated_client, user):
        roast = RoastRunFactory(submission__owner=user)
        ShareLinkFactory(roast=roast, owner=user)

        response = authenticated_client.get(f"/api/v1/share/roasts/{roast.id}/links/")

        assert response.status_code == 200
        assert response.json()["meta"]["count"] == 1


class TestShareLinkDetailView:
    def test_get_returns_detail(self, authenticated_client, user):
        roast = RoastRunFactory(submission__owner=user)
        link = ShareLinkFactory(roast=roast, owner=user)

        response = authenticated_client.get(f"/api/v1/share/links/{link.id}/")

        assert response.status_code == 200
        assert response.json()["data"]["token"] == link.token

    def test_delete_revokes_and_is_idempotent(self, authenticated_client, user):
        roast = RoastRunFactory(submission__owner=user)
        link = ShareLinkFactory(roast=roast, owner=user)

        first = authenticated_client.delete(f"/api/v1/share/links/{link.id}/")
        assert first.status_code == 204
        link.refresh_from_db()
        assert link.revoked_at is not None

        second = authenticated_client.delete(f"/api/v1/share/links/{link.id}/")
        assert second.status_code == 204

    def test_cannot_access_other_users_link(self, authenticated_client, user_factory):
        other = user_factory(email="share-owner3@example.com")
        roast = RoastRunFactory(submission__owner=other)
        link = ShareLinkFactory(roast=roast, owner=other)

        response = authenticated_client.get(f"/api/v1/share/links/{link.id}/")

        assert response.status_code == 404

    def test_detail_requires_authentication(self, api_client, user):
        roast = RoastRunFactory(submission__owner=user)
        link = ShareLinkFactory(roast=roast, owner=user)

        response = api_client.get(f"/api/v1/share/links/{link.id}/")

        assert response.status_code == 401
