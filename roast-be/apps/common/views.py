from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .health import check_celery, check_database, check_redis


@extend_schema(
    tags=["health"],
    responses={
        200: {
            "type": "object",
            "properties": {"status": {"type": "string"}, "version": {"type": "string"}},
        }
    },
)
class LivenessView(APIView):
    """
    Basic liveness: the process is up and able to handle a request at
    all. Deliberately does not touch the database/Redis — a slow or
    down dependency should surface via the readiness check, not make
    the process look dead to an orchestrator's liveness probe.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok", "version": settings.APP_VERSION})


@extend_schema(
    tags=["health"],
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "checks": {
                    "type": "object",
                    "properties": {
                        "database": {"type": "boolean"},
                        "redis": {"type": "boolean"},
                        "celery": {"type": "boolean"},
                    },
                },
            },
        }
    },
)
class ReadinessView(APIView):
    """
    Readiness: the process is up AND its runtime dependencies (database,
    Redis, and at least one live Celery worker) are reachable. Returns
    503 if any dependency is down, so an orchestrator can hold traffic
    without restarting the pod. `celery` checking worker liveness
    (not just broker reachability, which `redis` already covers) matters
    because apps.roasts/apps.extraction depend on a worker actually
    consuming tasks, not just a reachable queue.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        checks = {
            "database": check_database(),
            "redis": check_redis(),
            "celery": check_celery(),
        }
        is_ready = all(checks.values())
        return Response(
            {"status": "ok" if is_ready else "unavailable", "checks": checks},
            status=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
