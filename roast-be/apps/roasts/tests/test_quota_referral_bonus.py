import pytest

from apps.referrals.tests.factories import ReferralFactory
from apps.roasts.services import _enforce_weekly_quota, get_roast_quota_status
from apps.roasts.tests.factories import RoastRunFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _quota_settings(settings):
    settings.ROAST_WEEKLY_QUOTA = 3
    settings.REFERRAL_BONUS_AMOUNT = 4


class TestQuotaReflectsReferralBonus:
    def test_no_bonus_uses_base_limit(self, user):
        status = get_roast_quota_status(owner=user)
        assert status.limit == 3
        assert status.bonus_amount == 0
        assert status.bonus_expires_at is None

    def test_active_bonus_is_added_to_base_limit(self, user):
        referral = ReferralFactory(referred=user)
        status = get_roast_quota_status(owner=user)
        assert status.limit == 7
        assert status.bonus_amount == 4
        assert status.bonus_expires_at == referral.referred_bonus_expires_at

    def test_enforcement_uses_the_same_boosted_limit_as_display(self, user):
        """
        Regression test for the exact bug the implementation plan called
        out: get_roast_quota_status (display) and _enforce_weekly_quota
        (enforcement) must always agree on the effective limit. Without
        the referral bonus, the 4th roast in the window would be
        rejected; with a +4 bonus active, it must be allowed.
        """
        ReferralFactory(referred=user)
        for _ in range(6):
            RoastRunFactory(owner=user)

        status = get_roast_quota_status(owner=user)
        assert status.used == 6
        assert status.remaining == 1  # limit 7 - used 6

        from apps.accounts.models import User

        locked_owner = User.objects.select_for_update().get(id=user.id)
        # Must not raise — still under the boosted limit.
        _enforce_weekly_quota(locked_owner=locked_owner)

        RoastRunFactory(owner=user)  # 7th roast, now at the boosted limit
        locked_owner = User.objects.select_for_update().get(id=user.id)
        from rest_framework.exceptions import Throttled

        with pytest.raises(Throttled):
            _enforce_weekly_quota(locked_owner=locked_owner)
