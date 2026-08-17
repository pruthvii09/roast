import logging

import redis
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


def check_database() -> bool:
    try:
        connections["default"].cursor().execute("SELECT 1")
        return True
    except OperationalError:
        logger.exception("Readiness check: database connection failed")
        return False


def check_redis() -> bool:
    try:
        client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        return bool(client.ping())
    except redis.RedisError:
        logger.exception("Readiness check: redis connection failed")
        return False


def check_celery() -> bool:
    """
    Confirms at least one Celery worker is actually consuming tasks —
    check_redis() above only confirms the broker itself is reachable, so
    a fully-dead worker fleet with Redis still up would otherwise report
    "ready" while apps.roasts/apps.extraction's tasks silently queue
    forever. Tightly timeout-bounded (HEALTH_CHECK_CELERY_TIMEOUT_SECONDS,
    default ~1.5s) so a slow/absent worker can't stall the readiness
    endpoint itself.
    """
    try:
        from config import celery_app

        replies = celery_app.control.inspect(
            timeout=settings.HEALTH_CHECK_CELERY_TIMEOUT_SECONDS
        ).ping()
        return bool(replies)
    except Exception:
        logger.exception("Readiness check: celery inspect failed")
        return False
