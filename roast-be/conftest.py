import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def tmp_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    # DRF's throttle classes persist their request counters in the default
    # cache, which otherwise leaks state across tests (a test could get a
    # 429 because an earlier, unrelated test already used up the quota).
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory(db):
    return UserFactory


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def authenticated_client(user):
    # Deliberately a fresh APIClient, not the `api_client` fixture instance
    # — a test requesting both `api_client` and `authenticated_client`
    # needs them to be independent (one authenticated, one not).
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client
