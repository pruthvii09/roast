from .base import *  # noqa: F403
from .base import SPECTACULAR_SETTINGS  # noqa: F405

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or ["http://localhost:3000"]  # noqa: F405

# Local-dev-only convenience: browse the schema/Swagger/Redoc UI without
# needing a bearer token. base.py requires auth for these by default —
# this override is intentionally confined to dev.py and does not affect
# prod.py.
SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}
