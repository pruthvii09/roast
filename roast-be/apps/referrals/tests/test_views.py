import pytest

from ..models import ReferralCode

pytestmark = pytest.mark.django_db


class TestReferralInfoView:
    def test_returns_code_and_stats(self, authenticated_client, user):
        response = authenticated_client.get("/api/v1/referrals/me/")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["code"] == ReferralCode.objects.get(owner=user).code
        assert data["referral_url"].endswith(f"/register?ref={data['code']}")
        assert data["total_referred"] == 0
        assert data["total_qualified"] == 0

    def test_get_or_creates_a_stable_code_across_calls(self, authenticated_client):
        first = authenticated_client.get("/api/v1/referrals/me/").json()["data"]
        second = authenticated_client.get("/api/v1/referrals/me/").json()["data"]
        assert first["code"] == second["code"]

    def test_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/referrals/me/")
        assert response.status_code == 401

    def test_reflects_referral_stats(self, authenticated_client, user):
        from .factories import ReferralFactory

        ReferralFactory(referrer=user)
        response = authenticated_client.get("/api/v1/referrals/me/")
        assert response.json()["data"]["total_referred"] == 1
