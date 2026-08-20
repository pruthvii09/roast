import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User

from .models import Referral, ReferralCode

logger = logging.getLogger(__name__)

# No 0/O/1/I/L — this code is meant to be typed or read aloud, unlike
# apps.sharing.ShareLink.token (long, opaque, paste-only).
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8
_CODE_GENERATION_ATTEMPTS = 10


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def get_or_create_referral_code(*, user: User) -> ReferralCode:
    try:
        return ReferralCode.objects.get(owner=user)
    except ReferralCode.DoesNotExist:
        pass

    for _ in range(_CODE_GENERATION_ATTEMPTS):
        code = _generate_code()
        try:
            # A nested atomic() (a savepoint) is required here: without
            # it, catching IntegrityError below would leave the
            # surrounding transaction unusable for any further queries
            # on Postgres (a failed statement poisons the whole
            # transaction until rollback, not just the failed one).
            with transaction.atomic():
                return ReferralCode.objects.create(owner=user, code=code)
        except IntegrityError:
            # Either the code collided (retry with a new one) or a
            # concurrent request already created this user's row — check
            # for the latter before assuming it's a code collision.
            existing = ReferralCode.objects.filter(owner=user).first()
            if existing is not None:
                return existing
            continue

    raise RuntimeError("Could not generate a unique referral code after several attempts.")


def redeem_referral_code(*, referred: User, code: str | None) -> None:
    """
    Called once, immediately after `referred` registers. Silently no-ops
    on any missing/unknown/self-referral code — a bad `?ref=` value must
    never block or error out a real signup, and a hard error here would
    let someone probe which codes are valid. Callers must wrap this in
    their own try/except regardless (see apps.accounts.views.RegisterView)
    so an unexpected bug here can never break account creation.
    """
    if not code:
        return

    try:
        referral_code = ReferralCode.objects.select_related("owner").get(code=code)
    except ReferralCode.DoesNotExist:
        logger.info("Referral redemption: unknown code %r", code)
        return

    referrer = referral_code.owner
    if referrer.id == referred.id:
        logger.warning("Referral redemption: self-referral attempt ignored (user=%s)", referred.id)
        return

    now = timezone.now()
    try:
        # See get_or_create_referral_code's comment on why this needs its
        # own savepoint: without it, catching IntegrityError below would
        # leave the caller's transaction (RegisterView's request, in
        # practice) unusable for the response that still needs to be built.
        with transaction.atomic():
            Referral.objects.create(
                referrer=referrer,
                referred=referred,
                code=code,
                referred_bonus_expires_at=now + timedelta(days=settings.REFERRAL_BONUS_WINDOW_DAYS),
            )
    except IntegrityError:
        # `referred` already has a Referral row (OneToOneField) — should
        # be impossible for a brand-new user, but never let this crash
        # registration regardless of how it happened.
        logger.warning(
            "Referral redemption: referred user %s already has a referral", referred.id
        )
        return

    logger.info("Referral redeemed: referrer=%s referred=%s", referrer.id, referred.id)


def try_qualify_referral(*, referred: User) -> None:
    """
    Called after a RoastRun owned by `referred` reaches COMPLETED (see
    apps.roasts.tasks.process_roast_run). A no-op if `referred` isn't a
    referred user, or was already qualified.

    Grants the referrer's one-time bonus only on that referrer's FIRST
    qualifying referral ever — checked via a fresh existence query
    against `referrer_bonus_granted` across ALL of the referrer's rows,
    not a per-row DB constraint (this is a "first row wins" rule across
    multiple rows). Deliberately no select_for_update() here: two
    referred friends of the same referrer qualifying at the same moment
    is a low-stakes race — worst case both rows end up
    referrer_bonus_granted=True, but apps.referrals.selectors.
    get_active_referral_bonus takes the max expiry across matches, not a
    sum, so that race can never over-grant. Locking the referrer's User
    row here would also risk contending with
    apps.roasts.services._enforce_weekly_quota's own User row lock.
    """
    try:
        referral = Referral.objects.select_related("referrer").get(
            referred=referred, qualified_at__isnull=True
        )
    except Referral.DoesNotExist:
        return

    now = timezone.now()
    already_granted = Referral.objects.filter(
        referrer_id=referral.referrer_id, referrer_bonus_granted=True
    ).exists()

    update_fields = {"qualified_at": now}
    if not already_granted:
        update_fields["referrer_bonus_granted"] = True
        update_fields["referrer_bonus_expires_at"] = now + timedelta(
            days=settings.REFERRAL_BONUS_WINDOW_DAYS
        )

    Referral.objects.filter(pk=referral.pk).update(**update_fields)
    logger.info(
        "Referral qualified: referrer=%s referred=%s bonus_granted=%s",
        referral.referrer_id,
        referred.id,
        not already_granted,
    )
