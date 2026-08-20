import factory
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory

from ..models import Referral, ReferralCode


class ReferralCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReferralCode

    owner = factory.SubFactory(UserFactory)
    code = factory.Sequence(lambda n: f"CODE{n:04d}")


class ReferralFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Referral

    referrer = factory.SubFactory(UserFactory)
    referred = factory.SubFactory(UserFactory)
    code = factory.Sequence(lambda n: f"CODE{n:04d}")
    referred_bonus_expires_at = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=7)
    )
