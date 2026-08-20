from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # Superusers are created via a CLI command with no email flow behind
        # it — the OTP-verification login gate (see User.email_verified)
        # would otherwise lock out `manage.py createsuperuser`.
        extra_fields.setdefault("email_verified", True)
        return self.create_user(email, password, **extra_fields)


class User(TimeStampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    display_name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(max_length=2048, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Separate from `is_active` deliberately — `is_active` isn't used
    # anywhere else in this app today, and this keeps "hasn't verified
    # their email yet" from ever colliding with a future ban/suspend use
    # of is_active. Gates login: see apps.accounts.serializers.LoginSerializer.
    email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return self.email


class OTPPurpose(models.TextChoices):
    EMAIL_VERIFICATION = "email_verification", "Email verification"
    PASSWORD_RESET = "password_reset", "Password reset"


class EmailOTP(TimeStampedUUIDModel):
    """
    A one-time 6-digit code emailed to a user, for either purpose above.
    `code_hash` is a plain sha256 hex digest, not Django's (deliberately
    slow) password hasher — the defense here is expiry + `attempts` cap +
    endpoint throttling, not offline brute-force resistance, so a fast
    hash is the right tool. See apps.accounts.services.verify_otp for the
    single place this is checked/consumed.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    purpose = models.CharField(max_length=32, choices=OTPPurpose.choices)
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "accounts_emailotp"
        indexes = [
            models.Index(fields=["user", "purpose", "consumed_at"], name="otp_user_purpose_idx"),
        ]

    def __str__(self):
        return f"EmailOTP({self.user_id}, {self.purpose})"
