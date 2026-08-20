import pytest

from apps.referrals.models import Referral
from apps.referrals.services import get_or_create_referral_code

pytestmark = pytest.mark.django_db


def test_register_with_valid_referral_code_creates_referral(api_client, user):
    referral_code = get_or_create_referral_code(user=user)

    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "friend@example.com",
            "password": "Str0ngPassw0rd!",
            "referral_code": referral_code.code,
        },
    )

    assert response.status_code == 201
    referred_user_id = response.json()["data"]["id"]
    referral = Referral.objects.get(referred_id=referred_user_id)
    assert referral.referrer_id == user.id


def test_register_with_unknown_referral_code_still_succeeds(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "noref@example.com",
            "password": "Str0ngPassw0rd!",
            "referral_code": "BOGUSCOD",
        },
    )

    assert response.status_code == 201
    assert Referral.objects.filter(referred__email="noref@example.com").count() == 0


def test_register_referral_code_never_leaks_in_response(api_client, user):
    referral_code = get_or_create_referral_code(user=user)
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "friend2@example.com",
            "password": "Str0ngPassw0rd!",
            "referral_code": referral_code.code,
        },
    )
    assert "referral_code" not in response.json()["data"]
