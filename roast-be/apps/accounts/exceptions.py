from rest_framework.exceptions import AuthenticationFailed


class EmailNotVerifiedError(AuthenticationFailed):
    """
    Raised by LoginSerializer when the password is correct but
    User.email_verified is False — distinguishable from a wrong-password
    attempt via `api_error_code`, which
    apps.common.exception_handler._error_code_for reads generically
    (apps.common must never import from a domain app like this one).
    """

    api_error_code = "EMAIL_NOT_VERIFIED"
    default_detail = "Please verify your email before logging in."
    default_code = "email_not_verified"
