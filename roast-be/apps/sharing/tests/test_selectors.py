import pytest
from django.http import Http404
from django.utils import timezone

from apps.sharing.selectors import get_active_share_link_by_token, get_owned_share_links
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


class TestGetActiveShareLinkByToken:
    def test_returns_active_link(self):
        link = ShareLinkFactory()
        found = get_active_share_link_by_token(token=link.token)
        assert found.pk == link.pk

    def test_404_for_revoked_link(self):
        link = ShareLinkFactory(revoked_at=timezone.now())
        with pytest.raises(Http404):
            get_active_share_link_by_token(token=link.token)

    def test_404_for_unknown_token(self):
        with pytest.raises(Http404):
            get_active_share_link_by_token(token="does-not-exist")

    def test_404_when_submission_soft_deleted(self):
        link = ShareLinkFactory()
        link.roast.submission.soft_delete()
        with pytest.raises(Http404):
            get_active_share_link_by_token(token=link.token)


class TestGetOwnedShareLinks:
    def test_includes_revoked_and_submission_deleted_links(self):
        link = ShareLinkFactory()
        owner = link.owner
        link.revoked_at = timezone.now()
        link.save(update_fields=["revoked_at"])
        link.roast.submission.soft_delete()

        results = list(get_owned_share_links(owner=owner))

        assert results == [link]

    def test_excludes_other_owners_links(self):
        link = ShareLinkFactory()
        other_owner_link = ShareLinkFactory()

        results = list(get_owned_share_links(owner=link.owner))

        assert results == [link]
        assert other_owner_link not in results
