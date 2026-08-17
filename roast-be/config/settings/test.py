import tempfile

from .base import *  # noqa: F403

DEBUG = False

# CHECK constraints (e.g. Submission.source_url) are only enforced by
# Postgres, so tests must run against the real Postgres engine configured
# in base.py, not sqlite — do not override DATABASES here.

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

MEDIA_ROOT = tempfile.mkdtemp(prefix="roast_test_media_")

# base.py's default cache is Redis-backed (needed for correct throttling
# across multiple production processes) — tests don't need a shared cache
# across processes and shouldn't require a running Redis just to exercise
# throttle tests, so use the in-process default here instead.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
