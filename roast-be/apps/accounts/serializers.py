from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .exceptions import EmailNotVerifiedError
from .models import OTPPurpose, User
from .services import (
    change_password,
    confirm_email_verification,
    delete_user_account,
    generate_and_send_otp,
    reset_password_with_otp,
)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    # Not a User field — read separately by RegisterView (via
    # validated_data, before .save()) and handed to
    # apps.referrals.services.redeem_referral_code. Never validated
    # against real codes here: an invalid/unknown code must silently
    # no-op, not block registration (see redeem_referral_code's docstring).
    # max_length is generous (real codes are 8 chars) so a slightly
    # mistyped/garbled ?ref= value never turns into a validation error —
    # redeem_referral_code() already handles any unknown code as a silent
    # no-op; this just bounds request size, not correctness.
    referral_code = serializers.CharField(
        max_length=32, required=False, allow_blank=True, write_only=True
    )

    def validate_email(self, value):
        normalized = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        validated_data.pop("referral_code", None)
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "avatar_url", "email_verified", "created_at"]
        read_only_fields = fields


class LoginSerializer(TokenObtainPairSerializer):
    """
    Only intercepts one specific case: the submitted password is correct
    but the account's email isn't verified yet. Every other outcome
    (wrong password, unknown email, is_active=False) falls straight
    through to simplejwt's default authenticate()-based flow and its
    generic "no active account" error — deliberately, since simplejwt's
    ModelBackend-based check can't otherwise distinguish "wrong password"
    from "correct password but inactive", and this must not either (that
    distinction is only meaningful for the verified/unverified case).
    """

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs[self.username_field])
        except User.DoesNotExist:
            user = None

        if (
            user is not None
            and user.is_active
            and not user.email_verified
            and user.check_password(attrs["password"])
        ):
            raise EmailNotVerifiedError()

        return super().validate(attrs)


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["display_name", "avatar_url"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the current password."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        change_password(user=user, new_password=self.validated_data["new_password"])
        return user


class AccountDeleteSerializer(serializers.Serializer):
    """
    Requires the current password — defense against a leaked/stolen
    access token being used to instantly, irreversibly destroy an
    account (mirrors ChangePasswordSerializer's re-auth pattern).
    """

    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        delete_user_account(user=user, requesting_user=user)


class VerifyEmailSerializer(serializers.Serializer):
    """
    Unauthenticated — the user has no token yet at this point in the
    flow, so it looks the account up by email itself. Failure is always
    the same generic message regardless of whether the email doesn't
    exist, the code is wrong, or it's expired — never reveals which.
    """

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            user = None

        if user is None or not confirm_email_verification(user=user, code=attrs["code"]):
            # Keyed by field (matches ChangePasswordSerializer's convention
            # for validate()-level errors), not a bare string — a bare
            # string lands under "non_field_errors" instead, which the
            # frontend's applyApiFieldErrors can't map to the code input.
            raise serializers.ValidationError({"code": "Invalid or expired code."})

        attrs["user"] = user
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    """Always succeeds from the caller's perspective — see the view for why."""

    email = serializers.EmailField()

    def save(self, **kwargs):
        try:
            user = User.objects.get(email__iexact=self.validated_data["email"])
        except User.DoesNotExist:
            return
        if user.email_verified:
            return
        generate_and_send_otp(user=user, purpose=OTPPurpose.EMAIL_VERIFICATION)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Always succeeds from the caller's perspective — see the view for why."""

    email = serializers.EmailField()

    def save(self, **kwargs):
        try:
            user = User.objects.get(email__iexact=self.validated_data["email"])
        except User.DoesNotExist:
            return
        generate_and_send_otp(user=user, purpose=OTPPurpose.PASSWORD_RESET)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            user = None

        # Checked before touching the OTP (which would otherwise burn a
        # real attempt on what might just be a weak-password typo) —
        # Django's validators need a real user for similarity checks, so
        # this only runs when one was found; a missing user still falls
        # through to the same generic failure below either way. Caught
        # and re-raised keyed to "new_password" — django.core.exceptions.
        # ValidationError raised bare from inside validate() would
        # otherwise land under "non_field_errors" instead, same reasoning
        # as VerifyEmailSerializer's "code"-keyed error above.
        if user is not None:
            try:
                validate_password(attrs["new_password"], user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"new_password": list(exc.messages)}) from exc

        if user is None or not reset_password_with_otp(
            user=user, code=attrs["code"], new_password=attrs["new_password"]
        ):
            raise serializers.ValidationError({"code": "Invalid or expired code."})

        attrs["user"] = user
        return attrs
