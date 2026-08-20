import pytest
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory

from ..models import Referral, ReferralCode
from ..services import get_or_create_referral_code, redeem_referral_code, try_qualify_referral
from .factories import ReferralCodeFactory, ReferralFactory

pytestmark = pytest.mark.django_db


class TestGetOrCreateReferralCode:
    def test_creates_a_code_on_first_call(self, user):
        code = get_or_create_referral_code(user=user)
        assert code.owner_id == user.id
        assert len(code.code) == 8

    def test_is_idempotent(self, user):
        first = get_or_create_referral_code(user=user)
        second = get_or_create_referral_code(user=user)
        assert first.pk == second.pk
        assert ReferralCode.objects.filter(owner=user).count() == 1


class TestRedeemReferralCode:
    def test_creates_referral_with_immediate_referred_bonus(self):
        referrer = UserFactory()
        referral_code = ReferralCodeFactory(owner=referrer)
        referred = UserFactory()

        redeem_referral_code(referred=referred, code=referral_code.code)

        referral = Referral.objects.get(referred=referred)
        assert referral.referrer_id == referrer.id
        assert referral.referred_bonus_expires_at > timezone.now()
        assert referral.qualified_at is None
        assert referral.referrer_bonus_granted is False

    def test_missing_code_is_a_noop(self):
        referred = UserFactory()
        redeem_referral_code(referred=referred, code=None)
        redeem_referral_code(referred=referred, code="")
        assert Referral.objects.filter(referred=referred).count() == 0

    def test_unknown_code_is_a_noop(self):
        referred = UserFactory()
        redeem_referral_code(referred=referred, code="DOESNOTEXIST")
        assert Referral.objects.filter(referred=referred).count() == 0

    def test_self_referral_is_a_noop(self):
        user = UserFactory()
        referral_code = ReferralCodeFactory(owner=user)
        redeem_referral_code(referred=user, code=referral_code.code)
        assert Referral.objects.filter(referred=user).count() == 0

    def test_second_redemption_by_already_referred_user_is_a_noop(self):
        first_referrer_code = ReferralCodeFactory()
        second_referrer_code = ReferralCodeFactory()
        referred = UserFactory()

        redeem_referral_code(referred=referred, code=first_referrer_code.code)
        redeem_referral_code(referred=referred, code=second_referrer_code.code)

        assert Referral.objects.filter(referred=referred).count() == 1
        assert Referral.objects.get(referred=referred).referrer_id == first_referrer_code.owner_id


class TestTryQualifyReferral:
    def test_qualifies_and_grants_referrer_bonus_on_first_completion(self):
        referral = ReferralFactory()

        try_qualify_referral(referred=referral.referred)

        referral.refresh_from_db()
        assert referral.qualified_at is not None
        assert referral.referrer_bonus_granted is True
        assert referral.referrer_bonus_expires_at > timezone.now()

    def test_second_referred_friend_does_not_grant_a_second_bonus(self):
        referrer = UserFactory()
        first_referral = ReferralFactory(referrer=referrer)
        second_referral = ReferralFactory(referrer=referrer)

        try_qualify_referral(referred=first_referral.referred)
        try_qualify_referral(referred=second_referral.referred)

        first_referral.refresh_from_db()
        second_referral.refresh_from_db()
        assert first_referral.referrer_bonus_granted is True
        assert second_referral.qualified_at is not None
        assert second_referral.referrer_bonus_granted is False
        assert second_referral.referrer_bonus_expires_at is None

    def test_noop_for_a_user_who_was_never_referred(self, user):
        try_qualify_referral(referred=user)  # must not raise
        assert Referral.objects.count() == 0

    def test_noop_for_an_already_qualified_referral(self):
        referral = ReferralFactory(qualified_at=timezone.now(), referrer_bonus_granted=True)
        try_qualify_referral(referred=referral.referred)  # must not raise / re-grant
        assert Referral.objects.filter(referrer_bonus_granted=True).count() == 1
