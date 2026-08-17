import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.common.mixins import EnvelopeMixin

from .serializers import (
    AccountDeleteSerializer,
    ChangePasswordSerializer,
    MeUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)

# Minimal security audit trail: who did what, and whether it succeeded —
# never the credential/token content itself. Emails (unlike passwords or
# tokens) are standard, expected content for an auth audit log — this is
# what lets someone investigating credential-stuffing tell which account
# was targeted; it's unrelated to (and doesn't weaken) the "never leak
# emails via API responses" concern, which is about response bodies, not
# server-side logs only operators can read.


@extend_schema(tags=["auth"], responses=UserSerializer)
class RegisterView(EnvelopeMixin, generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("User registered", extra={"user_id": str(user.id), "email": user.email})
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["auth"])
class LoginView(EnvelopeMixin, TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-login"

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "") if hasattr(request.data, "get") else ""
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info("Login succeeded", extra={"email": email})
        else:
            logger.warning("Login failed", extra={"email": email})
        return response


@extend_schema(tags=["auth"])
class RefreshView(EnvelopeMixin, TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-refresh"


_LOGOUT_REQUEST_SCHEMA = {
    "application/json": {
        "type": "object",
        "properties": {"refresh": {"type": "string"}},
    }
}


@extend_schema(tags=["auth"], request=_LOGOUT_REQUEST_SCHEMA, responses={204: None})
class LogoutView(EnvelopeMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-logout"

    def post(self, request, *args, **kwargs):
        refresh = request.data.get("refresh")
        if not refresh:
            raise ValidationError({"refresh": "This field is required."})
        try:
            RefreshToken(refresh).blacklist()
        except TokenError as exc:
            # str(exc) here is simplejwt's own user-facing message (e.g.
            # "Token is invalid or expired") — safe to surface, same as
            # any other field-level validation message; raising through
            # DRF (rather than a hand-built Response) is what puts this
            # on the standard {"success": false, "error": {...}} envelope
            # like every other endpoint, instead of a bare {"refresh": ...}.
            raise ValidationError({"refresh": str(exc)}) from exc
        logger.info("User logged out", extra={"user_id": str(request.user.id)})
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["auth"],
    request={"DELETE": AccountDeleteSerializer},
    responses={204: None},
)
class MeView(EnvelopeMixin, generics.RetrieveUpdateAPIView):
    """
    GET    /api/v1/auth/me/ — the caller's own profile.
    PATCH  /api/v1/auth/me/ — update display_name/avatar_url.
    DELETE /api/v1/auth/me/ — permanently delete the caller's account and
           everything it owns (see apps.accounts.services.delete_user_account).
           Requires the current password in the body, same re-auth
           pattern as ChangePasswordView — irreversible, so a leaked
           access token alone isn't enough to trigger it.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        return MeUpdateSerializer if self.request.method == "PATCH" else UserSerializer

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(UserSerializer(self.get_object()).data)

    def delete(self, request, *args, **kwargs):
        serializer = AccountDeleteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user_id = str(request.user.id)
        serializer.save()
        logger.info("Account deleted", extra={"user_id": user_id})
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["auth"], request=ChangePasswordSerializer, responses={200: None})
class ChangePasswordView(EnvelopeMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-password-change"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Password changed", extra={"user_id": str(request.user.id)})
        return Response({"detail": "Password changed successfully."})
