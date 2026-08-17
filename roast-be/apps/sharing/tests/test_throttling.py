import pytest
from rest_framework.throttling import SimpleRateThrottle

from apps.roasts.tests.factories import RoastRunFactory
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


def _set_rate(monkeypatch, scope, rate):
    # See apps.accounts.tests.test_throttling._set_rate — ScopedRateThrottle.THROTTLE_RATES
    # is bound once at import time, so overriding settings.REST_FRAMEWORK at runtime
    # doesn't affect it; the shared dict itself must be patched instead.
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, scope, rate)


class TestShareThrottling:
    def test_share_link_create_is_throttled(self, authenticated_client, user, monkeypatch):
        _set_rate(monkeypatch, "share-link-create", "1/min")
        roast1 = RoastRunFactory(submission__owner=user)
        roast2 = RoastRunFactory(submission__owner=user)

        first = authenticated_client.post(f"/api/v1/share/roasts/{roast1.id}/links/")
        assert first.status_code == 201

        second = authenticated_client.post(f"/api/v1/share/roasts/{roast2.id}/links/")
        assert second.status_code == 429

    def test_share_public_view_is_throttled(self, api_client, monkeypatch):
        _set_rate(monkeypatch, "share-public-view", "1/min")
        link = ShareLinkFactory()

        first = api_client.get(f"/api/v1/share/public/{link.token}/")
        assert first.status_code == 200

        second = api_client.get(f"/api/v1/share/public/{link.token}/")
        assert second.status_code == 429

    def test_share_public_react_is_throttled(self, api_client, monkeypatch):
        _set_rate(monkeypatch, "share-public-react", "1/min")
        link = ShareLinkFactory()

        first = api_client.post(
            f"/api/v1/share/public/{link.token}/reactions/", {"reaction_type": "fire"}
        )
        assert first.status_code == 200

        second = api_client.post(
            f"/api/v1/share/public/{link.token}/reactions/", {"reaction_type": "fire"}
        )
        assert second.status_code == 429
