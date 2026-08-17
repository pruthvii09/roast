from rest_framework.exceptions import ValidationError


class FileValidationError(ValidationError):
    """Raised when an uploaded file fails size/type/content validation."""
