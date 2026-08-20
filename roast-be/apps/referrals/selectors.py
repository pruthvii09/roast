from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import User

from .models import Referral


@dataclass
class ReferralBonus:
    amount: int
    expires_at: datetime


def get_active_referral_bonus(*, user: User) -> ReferralBonus | None:
    """
    A user can have an active bonus from up to two roles at once — as
    the referred party (always eligible once referred, until it
    expires) and as a qualified referrer (only once
    Referral.referrer_bonus_granted is True for them). Never summed:
    the amount is always the flat settings.REFERRAL_BONUS_AMOUNT: if
    both roles are simultaneously active, only the later expiry wins.
    """
    now = timezone.now()
    expiries = []

    referred_row = Referral.objects.filter(referred=user, referred_bonus_expires_at__gt=now).first()
    if referred_row is not None:
        expiries.append(referred_row.referred_bonus_expires_at)

    referrer_row = (
        Referral.objects.filter(
            referrer=user, referrer_bonus_granted=True, referrer_bonus_expires_at__gt=now
        )
        .order_by("-referrer_bonus_expires_at")
        .first()
    )
    if referrer_row is not None:
        expiries.append(referrer_row.referrer_bonus_expires_at)

    if not expiries:
        return None
    return ReferralBonus(amount=settings.REFERRAL_BONUS_AMOUNT, expires_at=max(expiries))


def get_referral_stats(*, user: User) -> tuple[int, int]:
    """Returns (total_referred, total_qualified) for the referrals `user` has made."""
    qs = Referral.objects.filter(referrer=user)
    return qs.count(), qs.filter(qualified_at__isnull=False).count()
