import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory
from apps.roasts.models import RoastStatus
from apps.roasts.tests.factories import RoastRunFactory
from apps.sharing.exceptions import RoastNotShareableError
from apps.sharing.models import ShareLink
from apps.sharing.services import (
    create_or_get_share_link,
    get_public_roast_payload,
    get_reaction_totals,
    record_reaction,
    revoke_share_link,
)
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


class TestCreateOrGetShareLink:
    def test_creates_new_active_link(self):
        roast = RoastRunFactory()

        link, created = create_or_get_share_link(roast=roast, requesting_user=roast.owner)

        assert created is True
        assert link.revoked_at is None
        assert ShareLink.objects.filter(roast=roast).count() == 1

    def test_returns_existing_active_link_instead_of_duplicating(self):
        roast = RoastRunFactory()
        first, _ = create_or_get_share_link(roast=roast, requesting_user=roast.owner)

        second, created = create_or_get_share_link(roast=roast, requesting_user=roast.owner)

        assert created is False
        assert second.pk == first.pk
        assert ShareLink.objects.filter(roast=roast).count() == 1

    def test_rejects_non_completed_roast(self):
        roast = RoastRunFactory(status=RoastStatus.PROCESSING)
        with pytest.raises(RoastNotShareableError):
            create_or_get_share_link(roast=roast, requesting_user=roast.owner)

    def test_rejects_non_owner(self):
        roast = RoastRunFactory()
        other = UserFactory()
        with pytest.raises(PermissionDenied):
            create_or_get_share_link(roast=roast, requesting_user=other)


class TestRevokeShareLink:
    def test_sets_revoked_at(self):
        link = ShareLinkFactory()
        revoke_share_link(share_link=link, requesting_user=link.owner)
        link.refresh_from_db()
        assert link.revoked_at is not None

    def test_idempotent_repeat_revoke_does_not_move_timestamp(self):
        link = ShareLinkFactory()
        revoke_share_link(share_link=link, requesting_user=link.owner)
        link.refresh_from_db()
        first_revoked_at = link.revoked_at

        revoke_share_link(share_link=link, requesting_user=link.owner)
        link.refresh_from_db()

        assert link.revoked_at == first_revoked_at

    def test_rejects_non_owner(self):
        link = ShareLinkFactory()
        other = UserFactory()
        with pytest.raises(PermissionDenied):
            revoke_share_link(share_link=link, requesting_user=other)


class TestReactions:
    def test_record_reaction_creates_then_increments(self):
        link = ShareLinkFactory()

        totals = record_reaction(token=link.token, reaction_type="fire")
        assert totals["fire"] == 1

        totals = record_reaction(token=link.token, reaction_type="fire")
        assert totals["fire"] == 2

    def test_get_reaction_totals_seeds_every_type_at_zero(self):
        link = ShareLinkFactory()
        totals = get_reaction_totals(share_link=link)
        assert set(totals) == {"fire", "skull", "laughing", "clap"}
        assert all(v == 0 for v in totals.values())

    def test_404_reacting_to_revoked_link(self):
        link = ShareLinkFactory(revoked_at=timezone.now())
        with pytest.raises(Http404):
            record_reaction(token=link.token, reaction_type="fire")


class TestGetPublicRoastPayload:
    def test_increments_view_count(self):
        link = ShareLinkFactory()
        get_public_roast_payload(token=link.token)
        get_public_roast_payload(token=link.token)
        link.refresh_from_db()
        assert link.view_count == 2

    def test_404_for_revoked_token(self):
        link = ShareLinkFactory(revoked_at=timezone.now())
        with pytest.raises(Http404):
            get_public_roast_payload(token=link.token)
