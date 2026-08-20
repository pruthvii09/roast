from django.db import models

from apps.common.models import TimeStampedUUIDModel


class ReferralCode(TimeStampedUUIDModel):
    """
    One per user, created lazily (not at registration time) the first
    time they ask for their referral link — see
    apps.referrals.services.get_or_create_referral_code. `code` is short
    and drawn from an unambiguous alphabet (no 0/O/1/I/L) since it's
    meant to be typed or read aloud, unlike apps.sharing.ShareLink.token
    (long, opaque, paste-only).
    """

    owner = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="referral_code"
    )
    code = models.CharField(max_length=12, unique=True, editable=False)

    class Meta:
        db_table = "referrals_referralcode"

    def __str__(self):
        return self.code


class Referral(TimeStampedUUIDModel):
    """
    One row per successful code redemption, created once at the referred
    user's registration (apps.referrals.services.redeem_referral_code) —
    never later. `referred` is a OneToOneField: the core anti-abuse
    guarantee that a user can be the "referred" party at most once ever,
    enforced at the database level, not just in application code.

    Both bonuses are +settings.REFERRAL_BONUS_AMOUNT for
    settings.REFERRAL_BONUS_WINDOW_DAYS, but activate differently:
    - `referred_bonus_expires_at` is set immediately at creation — the
      referred friend's bonus starts the moment they sign up.
    - `referrer_bonus_granted`/`referrer_bonus_expires_at` stay unset
      until `qualified_at` is set (the referred friend's first RoastRun
      reaches COMPLETED — see apps.referrals.services.try_qualify_referral),
      and even then only for a referrer's FIRST-EVER qualifying referral:
      once any row for a given `referrer` has `referrer_bonus_granted=True`,
      later referrals by that same referrer are still recorded here (for
      stats) but never grant a second bonus — see try_qualify_referral's
      docstring for why this is enforced there rather than with a DB
      constraint (it's a "first row wins" rule across multiple rows, not
      a per-row invariant).
    """

    referrer = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="referrals_made"
    )
    referred = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="referred_by"
    )
    code = models.CharField(max_length=12)
    referred_bonus_expires_at = models.DateTimeField()
    qualified_at = models.DateTimeField(null=True, blank=True)
    referrer_bonus_granted = models.BooleanField(default=False)
    referrer_bonus_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "referrals_referral"
        indexes = [
            models.Index(
                fields=["referrer", "referrer_bonus_granted"], name="referral_referrer_granted_idx"
            ),
        ]

    def __str__(self):
        return f"Referral({self.referrer_id} -> {self.referred_id})"
