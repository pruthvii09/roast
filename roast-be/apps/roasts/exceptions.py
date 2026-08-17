from rest_framework.exceptions import ValidationError


class SubmissionNotRoastableError(ValidationError):
    """Raised when a roast is requested for a submission that isn't in a roastable state."""
