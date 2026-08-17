import pytest
from django.utils import timezone

from apps.roasts.tests.factories import RoastFindingFactory, RoastRunFactory, RoastSectionFactory
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


class TestPublicSharedRoastView:
    def test_returns_public_payload_shape(self, api_client):
        roast = RoastRunFactory()
        RoastSectionFactory(roast=roast)
        RoastFindingFactory(roast=roast)
        link = ShareLinkFactory(roast=roast)

        response = api_client.get(f"/api/v1/share/public/{link.token}/")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["summary"] == roast.summary
        assert data["final_verdict"] == roast.final_verdict
        assert data["score"] == roast.score
        assert len(data["sections"]) == 1
        assert len(data["findings"]) == 1
        assert set(data["reactions"]) == {"fire", "skull", "laughing", "clap"}

    def test_never_leaks_private_fields(self, api_client):
        roast = RoastRunFactory()
        link = ShareLinkFactory(roast=roast)

        response = api_client.get(f"/api/v1/share/public/{link.token}/")

        data = response.json()["data"]
        assert "id" not in data
        assert "owner" not in data
        assert "engine_version" not in data
        assert "error_message" not in data
        assert set(data["submission"]) == {"submission_type", "title"}
        assert "extracted_text" not in data["submission"]
        assert "metadata" not in data["submission"]
        assert "source_url" not in data["submission"]

    def test_increments_view_count(self, api_client):
        link = ShareLinkFactory()

        api_client.get(f"/api/v1/share/public/{link.token}/")
        link.refresh_from_db()

        assert link.view_count == 1

    def test_404_for_revoked_link(self, api_client):
        link = ShareLinkFactory(revoked_at=timezone.now())

        response = api_client.get(f"/api/v1/share/public/{link.token}/")

        assert response.status_code == 404

    def test_404_for_unknown_token(self, api_client):
        response = api_client.get("/api/v1/share/public/does-not-exist/")
        assert response.status_code == 404

    def test_no_authorization_header_required(self, api_client):
        link = ShareLinkFactory()
        response = api_client.get(f"/api/v1/share/public/{link.token}/")
        assert response.status_code == 200


class TestPublicReactionCreateView:
    def test_records_reaction_and_returns_totals(self, api_client):
        link = ShareLinkFactory()

        response = api_client.post(
            f"/api/v1/share/public/{link.token}/reactions/", {"reaction_type": "fire"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["fire"] == 1

    def test_404_reacting_to_revoked_link(self, api_client):
        link = ShareLinkFactory(revoked_at=timezone.now())

        response = api_client.post(
            f"/api/v1/share/public/{link.token}/reactions/", {"reaction_type": "fire"}
        )

        assert response.status_code == 404

    def test_rejects_invalid_reaction_type(self, api_client):
        link = ShareLinkFactory()

        response = api_client.post(
            f"/api/v1/share/public/{link.token}/reactions/", {"reaction_type": "bogus"}
        )

        assert response.status_code == 400
