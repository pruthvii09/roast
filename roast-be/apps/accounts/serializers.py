from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User
from .services import change_password, delete_user_account


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        normalized = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "avatar_url", "created_at"]
        read_only_fields = fields


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
