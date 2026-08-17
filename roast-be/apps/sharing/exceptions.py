from rest_framework.exceptions import ValidationError


class RoastNotShareableError(ValidationError):
    """Raised when a share link is requested for a roast that isn't completed yet."""
