from django.urls import path

from .views import (
    ChangePasswordView,
    ConfirmPasswordResetView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    RequestPasswordResetView,
    ResendVerificationEmailView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "verify-email/resend/",
        ResendVerificationEmailView.as_view(),
        name="auth-resend-verification",
    ),
    path(
        "password-reset/request/",
        RequestPasswordResetView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        ConfirmPasswordResetView.as_view(),
        name="auth-password-reset-confirm",
    ),
]
