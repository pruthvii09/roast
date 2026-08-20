import pytest
from django.db import IntegrityError

from ..models import Referral
from .factories import ReferralCodeFactory, ReferralFactory

pytestmark = pytest.mark.django_db


class TestReferralCode:
    def test_code_field_is_unique(self):
        ReferralCodeFactory(code="DUPLICAT")
        with pytest.raises(IntegrityError):
            ReferralCodeFactory(code="DUPLICAT")


class TestReferral:
    def test_a_user_can_only_be_referred_once(self):
        referral = ReferralFactory()
        with pytest.raises(IntegrityError):
            Referral.objects.create(
                referrer=referral.referrer,
                referred=referral.referred,
                code="ANOTHER1",
                referred_bonus_expires_at=referral.referred_bonus_expires_at,
            )
