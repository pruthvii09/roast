from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.mixins import EnvelopeMixin
from apps.common.pagination import StandardResultsSetPagination
from apps.submissions.selectors import get_owned_submission_or_404

from .models import RoastRun
from .permissions import IsRoastRunOwner
from .selectors import get_owned_roast_runs, get_roast_runs_for_submission
from .serializers import (
    RoastQuotaSerializer,
    RoastRunCreateSerializer,
    RoastRunListSerializer,
    RoastRunSerializer,
    RoastRunStatusSerializer,
)
from .services import create_roast_run, delete_roast_run, get_roast_quota_status


@extend_schema_view(
    get=extend_schema(tags=["roasts"], responses=RoastRunListSerializer),
    post=extend_schema(
        tags=["roasts"],
        request=RoastRunCreateSerializer,
        responses=RoastRunSerializer,
    ),
)
class SubmissionRoastRunListCreateView(EnvelopeMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/submissions/{submission_id}/roasts/  — list this
         submission's roast runs (owner-scoped).
    POST /api/v1/submissions/{submission_id}/roasts/  — create a queued
         RoastRun and dispatch asynchronous processing. Never calls an
         AI provider directly — that only happens inside the Celery
         task (apps.roasts.tasks.process_roast_run).
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    throttle_scope = "roast-create"

    def get_throttles(self):
        # Scoped throttle only on POST (create) — burst-rate defense in
        # depth on top of the weekly quota enforced in
        # apps.roasts.services.create_roast_run. GET (list) falls back to
        # the global default throttle.
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_submission(self):
        return get_owned_submission_or_404(
            owner=self.request.user, submission_id=self.kwargs["submission_id"]
        )

    def get_queryset(self):
        # Guards schema-generation introspection (drf-spectacular sets
        # swagger_fake_view) where request.user/kwargs aren't real.
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return RoastRun.objects.none()
        return get_roast_runs_for_submission(submission=self.get_submission())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RoastRunCreateSerializer
        return RoastRunListSerializer

    def create(self, request, *args, **kwargs):
        submission = self.get_submission()  # 404s if not found/not owned: "submission ownership"
        # ChoiceFields below enforce "supported language"/"supported intensity".
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        roast_run, created = create_roast_run(
            submission=submission,
            language=serializer.validated_data["language"],
            intensity=serializer.validated_data["intensity"],
        )
        out = RoastRunSerializer(roast_run, context={"request": request})
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(out.data, status=response_status)


@extend_schema(tags=["roasts"], responses=RoastQuotaSerializer)
class RoastQuotaView(EnvelopeMixin, APIView):
    """
    GET /api/v1/roasts/quota/ — the authenticated user's current weekly
    roast quota: limit/used/remaining/resets_at. Read-only, cheap (no
    row locking — see apps.roasts.services.get_roast_quota_status), safe
    to poll before deciding whether to show a "create roast" button as
    disabled.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        quota_status = get_roast_quota_status(owner=request.user)
        return Response(RoastQuotaSerializer(quota_status).data)


@extend_schema_view(
    get=extend_schema(tags=["roasts"], responses=RoastRunSerializer),
    delete=extend_schema(tags=["roasts"]),
)
class RoastRunDetailView(EnvelopeMixin, generics.RetrieveDestroyAPIView):
    """
    GET    /api/v1/roasts/{id}/ — full detail, including sections/findings.
    DELETE /api/v1/roasts/{id}/ — hard-deletes the run (cascades to its
           sections/findings).
    """

    permission_classes = [permissions.IsAuthenticated, IsRoastRunOwner]
    serializer_class = RoastRunSerializer
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return RoastRun.objects.none()
        return get_owned_roast_runs(owner=self.request.user)

    def perform_destroy(self, instance):
        delete_roast_run(roast_run=instance, requesting_user=self.request.user)


@extend_schema(tags=["roasts"], responses=RoastRunStatusSerializer)
class RoastRunStatusView(EnvelopeMixin, generics.RetrieveAPIView):
    """
    GET /api/v1/roasts/{id}/status/ — lightweight polling endpoint: just
    status/timestamps/error, no nested sections/findings. Intended for
    clients polling frequently while a run is queued/processing.
    """

    permission_classes = [permissions.IsAuthenticated, IsRoastRunOwner]
    serializer_class = RoastRunStatusSerializer
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return RoastRun.objects.none()
        return get_owned_roast_runs(owner=self.request.user)
