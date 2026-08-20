"""
Builds the HTML for OTP emails. Deliberately separate from
apps.notifications.emails — that module is pure Resend-sending infra with
zero domain content; this is where apps.accounts owns what its emails
actually say. Inline styles throughout (not a stylesheet) since most
email clients strip <style> blocks or ignore external CSS entirely.

Colors are the same hex conversion of app/globals.css's OKLCH brand
tokens already used for the frontend's generated OG card
(roast-fe/lib/og/colors.ts) — same brand, same numbers, just the Python
literal.
"""

from django.conf import settings

from .models import OTPPurpose

_COLOR_BACKGROUND = "#ffffff"
_COLOR_FOREGROUND = "#0a0a0a"
_COLOR_PRIMARY = "#464cb2"
_COLOR_MUTED = "#f5f5f5"
_COLOR_MUTED_FOREGROUND = "#737373"
_COLOR_BORDER = "#e5e5e5"

_COPY = {
    OTPPurpose.EMAIL_VERIFICATION: {
        "subject": "Verify your email — Roast Anything",
        "heading": "Verify your email",
        "body": "Enter this code to finish setting up your account and start getting roasted.",
    },
    OTPPurpose.PASSWORD_RESET: {
        "subject": "Reset your password — Roast Anything",
        "heading": "Reset your password",
        "body": "Enter this code to choose a new password.",
    },
}


def get_subject(*, purpose: str) -> str:
    return _COPY[purpose]["subject"]


def render_otp_email(*, code: str, purpose: str) -> str:
    copy = _COPY[purpose]
    spaced_code = " ".join(code)

    return f"""\
<div style="background-color: {_COLOR_MUTED}; padding: 40px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <div style="max-width: 480px; margin: 0 auto; background-color: {_COLOR_BACKGROUND}; border: 1px solid {_COLOR_BORDER}; border-radius: 16px; padding: 40px 32px;">
    <p style="margin: 0 0 32px; font-size: 18px; font-weight: 600; color: {_COLOR_FOREGROUND};">
      &#128293; Roast Anything
    </p>
    <h1 style="margin: 0 0 12px; font-size: 22px; font-weight: 600; color: {_COLOR_FOREGROUND};">
      {copy["heading"]}
    </h1>
    <p style="margin: 0 0 28px; font-size: 15px; line-height: 1.5; color: {_COLOR_MUTED_FOREGROUND};">
      {copy["body"]}
    </p>
    <div style="background-color: {_COLOR_MUTED}; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
      <span style="font-size: 32px; font-weight: 700; letter-spacing: 6px; color: {_COLOR_PRIMARY}; font-family: 'Courier New', monospace;">
        {spaced_code}
      </span>
    </div>
    <p style="margin: 0 0 4px; font-size: 13px; color: {_COLOR_MUTED_FOREGROUND};">
      This code expires in {settings.OTP_TTL_MINUTES} minutes.
    </p>
    <p style="margin: 24px 0 0; font-size: 12px; color: {_COLOR_MUTED_FOREGROUND}; border-top: 1px solid {_COLOR_BORDER}; padding-top: 16px;">
      If you didn't request this, you can safely ignore this email.
    </p>
  </div>
</div>
"""
