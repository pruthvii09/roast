from .base import *  # noqa: F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# Unlike base.py's DJANGO_SECRET_KEY (which has an insecure dev-only
# fallback so `manage.py` works out of the box locally), production must
# never silently start with that well-known string — require the real
# value with no default, exactly like ALLOWED_HOSTS above. Raises
# ImproperlyConfigured (django-environ) at settings-load time if unset.
SECRET_KEY = env("DJANGO_SECRET_KEY")

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# Exempted because both the `web` service's Docker HEALTHCHECK and
# scripts/deploy.sh's readiness probe hit these paths over plain HTTP
# directly against the container (bypassing Caddy, which is what sets
# X-Forwarded-Proto for real traffic) — without this they'd always be
# redirected to https and fail, since gunicorn itself only serves HTTP.
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/"]
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 7)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CORS_ALLOW_ALL_ORIGINS = False  # rely solely on the explicit CORS_ALLOWED_ORIGINS allowlist

# Assumes TLS is terminated upstream (a load balancer / reverse proxy),
# matching the plain-gunicorn prod Docker target (see docker/Dockerfile) —
# without this, Django can't tell an already-HTTPS request (proxied to it
# over plain HTTP internally) from a real HTTP one, which breaks
# SECURE_SSL_REDIRECT above (infinite redirect loop) and secure-cookie
# logic. Only trust this header if the proxy is configured to always set
# it and strip any client-supplied value — the ONLY safe way to use
# SECURE_PROXY_SSL_HEADER at all.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Needed only if the Django admin (session+CSRF-cookie authenticated,
# unlike the JWT-bearer API) is ever exposed through that same proxy on a
# host Django doesn't already trust via ALLOWED_HOSTS scheme-matching.
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
