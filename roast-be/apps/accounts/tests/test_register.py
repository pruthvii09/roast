import pytest

from apps.accounts.models import EmailOTP, OTPPurpose, User

pytestmark = pytest.mark.django_db


def test_register_happy_path(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "new@example.com", "password": "Str0ngPassw0rd!", "display_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "new@example.com"
    assert "password" not in body["data"]


def test_register_creates_unverified_user_with_pending_otp(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "unverified-new@example.com", "password": "Str0ngPassw0rd!"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["email_verified"] is False

    user = User.objects.get(email="unverified-new@example.com")
    assert EmailOTP.objects.filter(
        user=user, purpose=OTPPurpose.EMAIL_VERIFICATION, consumed_at__isnull=True
    ).exists()


def test_register_then_login_before_verifying_is_rejected(api_client):
    api_client.post(
        "/api/v1/auth/register/",
        {"email": "cant-login-yet@example.com", "password": "Str0ngPassw0rd!"},
    )
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "cant-login-yet@example.com", "password": "Str0ngPassw0rd!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_register_duplicate_email_rejected(api_client, user_factory):
    user_factory(email="dupe@example.com")
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "dupe@example.com", "password": "Str0ngPassw0rd!"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_weak_password_rejected(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "weak@example.com", "password": "123"},
    )
    assert response.status_code == 400


def test_register_missing_fields_rejected(api_client):
    response = api_client.post("/api/v1/auth/register/", {})
    assert response.status_code == 400
