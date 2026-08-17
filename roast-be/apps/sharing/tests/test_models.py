import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.roasts.tests.factories import RoastRunFactory
from apps.sharing.models import Reaction, ReactionType, ShareLink
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


class TestShareLinkConstraints:
    def test_only_one_active_link_per_roast(self):
        roast = RoastRunFactory()
        ShareLinkFactory(roast=roast)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ShareLinkFactory(roast=roast)

    def test_new_active_link_allowed_after_revoke(self):
        roast = RoastRunFactory()
        first = ShareLinkFactory(roast=roast)
        first.revoked_at = timezone.now()
        first.save(update_fields=["revoked_at"])

        second = ShareLinkFactory(roast=roast)

        assert second.revoked_at is None
        assert ShareLink.objects.filter(roast=roast).count() == 2


class TestReactionConstraints:
    def test_only_one_reaction_row_per_type_per_link(self):
        share_link = ShareLinkFactory()
        Reaction.objects.create(share_link=share_link, reaction_type=ReactionType.FIRE, count=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Reaction.objects.create(
                    share_link=share_link, reaction_type=ReactionType.FIRE, count=1
                )
