from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
APP_VERSION = env("APP_VERSION", default="1.0.0")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
    # local
    "apps.common",
    "apps.accounts",
    "apps.submissions",
    "apps.extraction",
    "apps.roasts",
    "apps.ai",
    "apps.sharing",
    "apps.feedback",
    "apps.referrals",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.common.middleware.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="roast_anything"),
        "USER": env("POSTGRES_USER", default="roast"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="roast"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --------------------------------------------------------------------------
# Internationalization
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static / media
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Health checks
# --------------------------------------------------------------------------
HEALTH_CHECK_CELERY_TIMEOUT_SECONDS = env.float("HEALTH_CHECK_CELERY_TIMEOUT_SECONDS", default=1.5)

# --------------------------------------------------------------------------
# Cache
#
# DRF's throttle classes (see REST_FRAMEWORK/DEFAULT_THROTTLE_CLASSES
# below) store their request counters in the default cache. Left
# unconfigured, Django falls back to a per-process LocMemCache — which
# means throttling silently doesn't work correctly across multiple
# gunicorn worker processes (each process would have its own independent
# counters), only appearing to work in a single-process dev server. Redis
# is already required infrastructure (Celery broker); reusing it here on
# its own DB index (distinct from the broker/result-backend DBs below)
# needs no new dependency (Django 5.1+ ships a built-in Redis cache
# backend). test.py overrides this back to LocMemCache — tests don't need
# a shared cache across processes.
# --------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("DJANGO_CACHE_URL", default="redis://localhost:6379/2"),
    }
}

# --------------------------------------------------------------------------
# DRF
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.common.exception_handler.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    # Global baseline throttle: covers every view that doesn't set its own
    # throttle_classes (a view-level throttle_classes list fully replaces
    # this default, it doesn't add to it — so auth/submission/roast views
    # below, which set tighter scoped throttles, are unaffected by these
    # generous baseline rates; this exists purely to close the gap for
    # views with no throttle at all, e.g. GET endpoints).
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "user": env("THROTTLE_DEFAULT_USER", default="300/hour"),
        "anon": env("THROTTLE_DEFAULT_ANON", default="60/hour"),
        "auth-register": env("THROTTLE_AUTH_REGISTER", default="10/hour"),
        "auth-login": env("THROTTLE_AUTH_LOGIN", default="10/min"),
        "auth-refresh": env("THROTTLE_AUTH_REFRESH", default="30/min"),
        "auth-logout": env("THROTTLE_AUTH_LOGOUT", default="30/min"),
        "auth-password-change": env("THROTTLE_AUTH_PASSWORD_CHANGE", default="5/hour"),
        "auth-verify-email": env("THROTTLE_AUTH_VERIFY_EMAIL", default="10/hour"),
        "auth-resend-otp": env("THROTTLE_AUTH_RESEND_OTP", default="3/hour"),
        "auth-password-reset-request": env(
            "THROTTLE_AUTH_PASSWORD_RESET_REQUEST", default="5/hour"
        ),
        "auth-password-reset-confirm": env(
            "THROTTLE_AUTH_PASSWORD_RESET_CONFIRM", default="10/hour"
        ),
        "submission-create": env("THROTTLE_SUBMISSION_CREATE", default="20/hour"),
        "roast-create": env("THROTTLE_ROAST_CREATE", default="10/hour"),
        "share-link-create": env("THROTTLE_SHARE_LINK_CREATE", default="20/hour"),
        "share-public-view": env("THROTTLE_SHARE_PUBLIC_VIEW", default="120/hour"),
        "share-public-react": env("THROTTLE_SHARE_PUBLIC_REACT", default="30/hour"),
        "wall-of-fame-list": env("THROTTLE_WALL_OF_FAME_LIST", default="120/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Roast Anything API",
    "DESCRIPTION": "Backend API for the Roast Anything AI roasting platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # drf-spectacular's own default is AllowAny for its schema/Swagger/
    # Redoc views, which would silently override this project's global
    # IsAuthenticated default and expose the full API surface (every
    # endpoint path, field name/type, enum value) to anyone, unauthenticated,
    # in every environment. Require auth by default; dev.py relaxes this
    # back to AllowAny for local convenience only.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
    # Submission.status and RoastRun.status are different enums that
    # happen to share the field name "status" — without this, schema
    # generation resolves the naming collision with an opaque
    # auto-generated name (e.g. "Status640Enum").
    "ENUM_NAME_OVERRIDES": {
        "SubmissionStatusEnum": "apps.submissions.models.SubmissionStatus",
        "RoastStatusEnum": "apps.roasts.models.RoastStatus",
        "ExtractionStatusEnum": "apps.extraction.models.ExtractionStatus",
    },
}

# --------------------------------------------------------------------------
# Celery
# --------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Bounds how long a client-side dispatch (e.g. .apply_async in an HTTP
# request) can block trying to reach a broker that's down — without this,
# kombu's connection-retry backoff can hold a request open for 15-20s
# before finally raising, which apps.roasts.services relies on failing
# fast so it can mark the RoastRun `failed` instead of hanging the
# response. This does not apply to the worker's own broker connection
# (governed by CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP above).
CELERY_BROKER_CONNECTION_TIMEOUT = 2
CELERY_BROKER_CONNECTION_MAX_RETRIES = 1
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "socket_connect_timeout": 2,
    "socket_timeout": 2,
    "max_retries": 1,
}

# Both process_roast_run and extract_submission_task claim their row via
# a conditional "queued -> processing" UPDATE specifically so they're safe
# to run more than once for the same id — a design that only pays off if
# Celery's delivery is actually at-least-once. By default it isn't: Celery
# acks a message as soon as a worker *receives* it (task_acks_late=False),
# so a worker killed mid-task (OOM, SIGKILL, host failure) loses the
# message entirely rather than it being redelivered. task_acks_late=True
# (message acked only after the task returns) + task_reject_on_worker_lost
# (a killed worker's unacked message is explicitly requeued, not left
# ambiguous) together make the "at-least-once" the claim pattern already
# assumes actually true. worker_prefetch_multiplier=1 pairs with
# acks_late so one worker can't hoard several unacked tasks at once.
# This narrows, but does not close, the "worker dies mid-task" gap: once
# a task HAS claimed a row (flipped it to `processing`), a retry/redelivery
# of that same message will see 0 rows to claim and safely no-op rather
# than actually resuming — the claim pattern is deliberately not designed
# to survive that. The actual backstop for a task that dies *after*
# claiming is the Beat reconciliation sweep below (CELERY_BEAT_SCHEDULE),
# which fails any row stuck in queued/processing past a generous
# staleness threshold.
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Reconciliation sweeps (apps.roasts.tasks.reconcile_stuck_roast_runs,
# apps.extraction.tasks.reconcile_stuck_extraction_tasks) — see the
# comment above. Requires a `celery -A config beat` process running
# alongside the worker(s); see docker-compose.prod.yml.
CELERY_BEAT_SCHEDULE = {
    "reconcile-stuck-roast-runs": {
        "task": "apps.roasts.reconcile_stuck_roast_runs",
        "schedule": 300.0,
    },
    "reconcile-stuck-extraction-tasks": {
        "task": "apps.extraction.reconcile_stuck_extraction_tasks",
        "schedule": 300.0,
    },
}

# --------------------------------------------------------------------------
# Storage / uploads
# --------------------------------------------------------------------------
STORAGE_BACKEND = env("STORAGE_BACKEND", default="local")
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))
MEDIA_URL = "media/"  # not served directly; downloads are gated through the API

if STORAGE_BACKEND == "cloudinary":
    # No defaults: fail fast at settings-load time if this backend is
    # selected but misconfigured, rather than at first upload — mirrors
    # prod.py's DJANGO_SECRET_KEY = env("DJANGO_SECRET_KEY") pattern.
    CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET")
else:
    CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME", default="")
    CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY", default="")
    CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET", default="")

CLOUDINARY_HTTP_TIMEOUT_SECONDS = env.float("CLOUDINARY_HTTP_TIMEOUT_SECONDS", default=10.0)

MAX_UPLOAD_SIZE_BYTES = env.int("MAX_UPLOAD_SIZE_BYTES", default=10 * 1024 * 1024)
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_BYTES

# Separate, much smaller cap for non-file request bodies (JSON/form POST
# data) — Django's file-upload handling is governed by
# FILE_UPLOAD_MAX_MEMORY_SIZE above, not this setting, so lowering this
# independently doesn't affect resume uploads. 10MB (the file-upload
# default) is unnecessarily generous for endpoints like /auth/login/ that
# only ever receive a few small fields.
MAX_JSON_BODY_SIZE_BYTES = env.int("MAX_JSON_BODY_SIZE_BYTES", default=1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_JSON_BODY_SIZE_BYTES

ALLOWED_RESUME_CONTENT_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
ALLOWED_RESUME_EXTENSIONS = [".pdf", ".doc", ".docx"]

# --------------------------------------------------------------------------
# Document extraction pipeline (apps.extraction)
#
# Bounds how long a single asynchronous extraction task may run before
# Celery kills it — protection against a pathological file (e.g. a
# PDF crafted to hang a parser) stalling a worker indefinitely.
# soft_time_limit raises SoftTimeLimitExceeded inside the task (caught
# and recorded as a normal extraction failure); time_limit is Celery's
# hard SIGKILL backstop, kept a little above the soft limit so the task
# always gets a chance to record its own failure first.
# --------------------------------------------------------------------------
EXTRACTION_TASK_SOFT_TIME_LIMIT_SECONDS = env.float(
    "EXTRACTION_TASK_SOFT_TIME_LIMIT_SECONDS", default=25.0
)
EXTRACTION_TASK_TIME_LIMIT_SECONDS = env.float("EXTRACTION_TASK_TIME_LIMIT_SECONDS", default=35.0)

# Timeout/size caps for any outbound HTTP call a processor makes
# (WebsiteProcessor fetching a submitted URL, GitHubProcessor calling the
# GitHub API) — never let a slow/huge remote response stall or bloat an
# extraction task. EXTRACTION_MAX_TEXT_CHARS caps the *normalized* text
# a processor stores (see apps.extraction.text_utils.normalize_text),
# separate from the raw-response byte cap above it.
EXTRACTION_HTTP_TIMEOUT_SECONDS = env.float("EXTRACTION_HTTP_TIMEOUT_SECONDS", default=10.0)
EXTRACTION_HTTP_MAX_RESPONSE_BYTES = env.int(
    "EXTRACTION_HTTP_MAX_RESPONSE_BYTES", default=1_000_000
)
EXTRACTION_MAX_TEXT_CHARS = env.int("EXTRACTION_MAX_TEXT_CHARS", default=20_000)

# GitHubProcessor config. EXTRACTION_GITHUB_ACCESS_TOKEN is optional —
# unset (default) means anonymous GitHub API calls, subject to GitHub's
# ~60 requests/hour/IP unauthenticated rate limit. This is also the seam
# a future per-user OAuth flow would use instead of one shared token —
# see apps.extraction.processors.github.GitHubProcessor's docstring.
EXTRACTION_GITHUB_API_BASE_URL = env(
    "EXTRACTION_GITHUB_API_BASE_URL", default="https://api.github.com"
)
EXTRACTION_GITHUB_ACCESS_TOKEN = env("EXTRACTION_GITHUB_ACCESS_TOKEN", default="")

# --------------------------------------------------------------------------
# AI provider config
#
# AI_PROVIDER selects the apps.ai.providers.get_ai_provider() factory
# branch. "stub" (default) always fails with AIProviderError — useful for
# dev/CI without an API key. "openai" uses the real OpenAI Chat
# Completions API via apps.ai.providers.openai.OpenAIProvider.
# --------------------------------------------------------------------------
AI_PROVIDER = env("AI_PROVIDER", default="stub")
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
AI_OPENAI_MODEL = env("AI_OPENAI_MODEL", default="gpt-4o-mini")
AI_OPENAI_TEMPERATURE = env.float("AI_OPENAI_TEMPERATURE", default=0.9)
AI_OPENAI_MAX_OUTPUT_TOKENS = env.int("AI_OPENAI_MAX_OUTPUT_TOKENS", default=2000)

# Per-1000-token USD pricing for whichever model AI_OPENAI_MODEL names —
# a single current/configured model's price, not a multi-model table,
# since only one model is ever active at a time. Defaults are
# approximate gpt-4o-mini-class pricing; check current vendor pricing
# before relying on these for real billing.
AI_OPENAI_INPUT_PRICE_PER_1K = env.float("AI_OPENAI_INPUT_PRICE_PER_1K", default=0.00015)
AI_OPENAI_OUTPUT_PRICE_PER_1K = env.float("AI_OPENAI_OUTPUT_PRICE_PER_1K", default=0.0006)

# Request-level timeout for a single AI provider call.
AI_REQUEST_TIMEOUT_SECONDS = env.float("AI_REQUEST_TIMEOUT_SECONDS", default=30.0)

# Bounded + exponential retry policy shared by both failure classes the
# roasting service retries on: transient provider errors (timeout,
# connection error) and malformed/invalid structured output. Delay
# before attempt N (N>1) is AI_RETRY_BACKOFF_BASE_SECONDS * 2**(N-2).
AI_MAX_ATTEMPTS = env.int("AI_MAX_ATTEMPTS", default=3)
AI_RETRY_BACKOFF_BASE_SECONDS = env.float("AI_RETRY_BACKOFF_BASE_SECONDS", default=2.0)

# Source text handed to the model is capped to control token cost/abuse —
# longer submissions are truncated (with a note in the prompt), not
# rejected.
AI_MAX_SOURCE_TEXT_CHARS = env.int("AI_MAX_SOURCE_TEXT_CHARS", default=8000)

# Tag recorded on every RoastRun so generated content stays reproducible/
# auditable regardless of which "engine" (stub or a real provider) ran.
ROAST_ENGINE_VERSION = env("ROAST_ENGINE_VERSION", default="v1")

# Weekly per-user roast quota (apps.roasts.services.create_roast_run) —
# every roast-creation attempt counts against it, including ones that
# later fail, in a rolling (not calendar) window. Exists to bound AI
# provider cost/abuse from a single account; see GET /api/v1/roasts/quota/
# for a way to check remaining quota ahead of a 429.
ROAST_WEEKLY_QUOTA = env.int("ROAST_WEEKLY_QUOTA", default=3)
ROAST_QUOTA_WINDOW_DAYS = env.int("ROAST_QUOTA_WINDOW_DAYS", default=7)

# Referral bonus (apps.referrals) — added on top of ROAST_WEEKLY_QUOTA for
# REFERRAL_BONUS_WINDOW_DAYS when a referral is active; see
# apps.referrals.selectors.get_active_referral_bonus and
# apps.roasts.services._effective_weekly_limit for how the two combine.
REFERRAL_BONUS_AMOUNT = env.int("REFERRAL_BONUS_AMOUNT", default=1)
REFERRAL_BONUS_WINDOW_DAYS = env.int("REFERRAL_BONUS_WINDOW_DAYS", default=7)

# Same purpose as EXTRACTION_TASK_*_TIME_LIMIT_SECONDS above: bounds how
# long a single process_roast_run execution may run (the AI provider call
# itself is already bounded by AI_REQUEST_TIMEOUT_SECONDS x AI_MAX_ATTEMPTS
# below, but this is the outer Celery-level backstop against the task
# hanging for any other reason).
ROAST_TASK_SOFT_TIME_LIMIT_SECONDS = env.float("ROAST_TASK_SOFT_TIME_LIMIT_SECONDS", default=90.0)
ROAST_TASK_TIME_LIMIT_SECONDS = env.float("ROAST_TASK_TIME_LIMIT_SECONDS", default=120.0)

# Staleness thresholds for the Beat reconciliation sweeps (see the
# CELERY_TASK_ACKS_LATE comment above for why these exist) — comfortably
# above each task's own time limit so a task that's still legitimately
# running is never mistaken for stuck.
ROAST_STUCK_THRESHOLD_MINUTES = env.int("ROAST_STUCK_THRESHOLD_MINUTES", default=15)
EXTRACTION_STUCK_THRESHOLD_MINUTES = env.int("EXTRACTION_STUCK_THRESHOLD_MINUTES", default=15)

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=False)

# --------------------------------------------------------------------------
# Sharing
# --------------------------------------------------------------------------
# Base URL of the frontend, used to build the public share_url returned by
# apps.sharing.serializers.ShareLinkSerializer (e.g. f"{FRONTEND_SHARE_BASE_URL}/r/{token}").
FRONTEND_SHARE_BASE_URL = env("FRONTEND_SHARE_BASE_URL", default="http://localhost:3000")

# --------------------------------------------------------------------------
# Transactional email (apps.notifications) — Resend is the only email
# backend; there is no SMTP/Django-email-backend configuration anywhere.
# DEFAULT_FROM_EMAIL's domain must be verified in the Resend dashboard.
# --------------------------------------------------------------------------
RESEND_API_KEY = env("RESEND_API_KEY", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# --------------------------------------------------------------------------
# Email OTP (apps.accounts) — email verification (required before first
# login) and password reset both share one EmailOTP model/verify_otp()
# service function, distinguished only by `purpose`.
# --------------------------------------------------------------------------
OTP_TTL_MINUTES = env.int("OTP_TTL_MINUTES", default=10)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)

# --------------------------------------------------------------------------
# Logging
#
# Policy: never pass submission file bytes, extracted document text,
# AI prompts, or AI outputs containing private user content to any
# logger call — metadata only (ids, status, exception class, token
# counts, latency). Enforced by convention/review, not tooling: see
# apps.extraction.services and apps.ai.services.roasting/extraction for
# the code paths this applies to.
# --------------------------------------------------------------------------
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "apps.common.logging_formatters.JSONFormatter",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["console"], "level": DJANGO_LOG_LEVEL},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
