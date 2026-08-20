import pytest
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory

from ..selectors import get_active_referral_bonus, get_referral_stats
from .factories import ReferralFactory

pytestmark = pytest.mark.django_db


class TestGetActiveReferralBonus:
    def test_none_when_no_referral_exists(self, user):
        assert get_active_referral_bonus(user=user) is None

    def test_active_for_referred_user_immediately(self):
        referral = ReferralFactory()
        bonus = get_active_referral_bonus(user=referral.referred)
        assert bonus is not None
        assert bonus.amount == 1
        assert bonus.expires_at == referral.referred_bonus_expires_at

    def test_expired_referred_bonus_is_ignored(self):
        referral = ReferralFactory(
            referred_bonus_expires_at=timezone.now() - timezone.timedelta(days=1)
        )
        assert get_active_referral_bonus(user=referral.referred) is None

    def test_referrer_bonus_only_active_once_granted(self):
        referral = ReferralFactory()
        assert get_active_referral_bonus(user=referral.referrer) is None

        referral.referrer_bonus_granted = True
        referral.referrer_bonus_expires_at = timezone.now() + timezone.timedelta(days=7)
        referral.save()

        bonus = get_active_referral_bonus(user=referral.referrer)
        assert bonus is not None
        assert bonus.amount == 1

    def test_takes_later_expiry_when_both_roles_active(self):
        user = UserFactory()
        later = timezone.now() + timezone.timedelta(days=10)
        earlier = timezone.now() + timezone.timedelta(days=2)

        # `user` was referred (bonus expires `earlier`)...
        ReferralFactory(referred=user, referred_bonus_expires_at=earlier)
        # ...and is also a qualified referrer of someone else (expires `later`).
        ReferralFactory(referrer=user, referrer_bonus_granted=True, referrer_bonus_expires_at=later)

        bonus = get_active_referral_bonus(user=user)
        assert bonus.amount == 1  # never summed
        assert bonus.expires_at == later


class TestGetReferralStats:
    def test_counts_total_and_qualified(self):
        referrer = UserFactory()
        ReferralFactory(referrer=referrer, qualified_at=timezone.now())
        ReferralFactory(referrer=referrer, qualified_at=None)
        ReferralFactory()  # unrelated referrer

        total, qualified = get_referral_stats(user=referrer)
        assert total == 2
        assert qualified == 1
