from django.http import FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.mixins import EnvelopeMixin
from apps.common.pagination import StandardResultsSetPagination

from .filters import SubmissionFilter
from .models import Submission
from .permissions import IsSubmissionOwner
from .selectors import get_owned_asset_or_404, get_owned_submissions
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionListSerializer,
    SubmissionSerializer,
    SubmissionStatusSerializer,
    SubmissionUpdateSerializer,
)
from .services import delete_submission, get_asset_stream


@extend_schema_view(
    list=extend_schema(tags=["submissions"], responses=SubmissionListSerializer),
    retrieve=extend_schema(tags=["submissions"], responses=SubmissionSerializer),
    create=extend_schema(
        tags=["submissions"],
        request=SubmissionCreateSerializer,
        responses=SubmissionSerializer,
    ),
    partial_update=extend_schema(
        tags=["submissions"],
        request=SubmissionUpdateSerializer,
        responses=SubmissionSerializer,
    ),
    destroy=extend_schema(tags=["submissions"]),
)
class SubmissionViewSet(EnvelopeMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsSubmissionOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionFilter
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = StandardResultsSetPagination
    throttle_scope = "submission-create"

    def get_throttles(self):
        # Only creation is scope-throttled here (it uploads a file and/or
        # dispatches an async extraction task, unlike list/retrieve/update/
        # delete) — everything else falls back to the global default
        # throttle (see REST_FRAMEWORK.DEFAULT_THROTTLE_CLASSES).
        if self.action == "create":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        # Guards against schema-generation introspection (drf-spectacular
        # sets swagger_fake_view) and any other path where request.user
        # isn't a real authenticated User — filtering by an AnonymousUser
        # would otherwise raise trying to use it as a UUID FK value.
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Submission.objects.none()
        return get_owned_submissions(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissionCreateSerializer
        if self.action == "partial_update":
            return SubmissionUpdateSerializer
        if self.action == "list":
            return SubmissionListSerializer
        return SubmissionSerializer

    def perform_destroy(self, instance):
        delete_submission(submission=instance, requesting_user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        out = SubmissionSerializer(submission, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        out = SubmissionSerializer(submission, context={"request": request})
        return Response(out.data)


@extend_schema(tags=["submissions"], responses=SubmissionStatusSerializer)
class SubmissionStatusView(EnvelopeMixin, generics.RetrieveAPIView):
    """
    GET /api/v1/submissions/{id}/status/ — lightweight polling endpoint:
    just status/error/timestamps, no extracted_text/metadata. Intended
    for clients polling frequently while a resume's extraction runs in
    the background — mirrors apps.roasts.views.RoastRunStatusView.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubmissionOwner]
    serializer_class = SubmissionStatusSerializer
    lookup_url_kwarg = "submission_id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Submission.objects.none()
        return get_owned_submissions(owner=self.request.user)


@extend_schema(
    tags=["submissions"],
    responses={200: OpenApiTypes.BINARY},
)
class AssetDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id, asset_id):
        asset = get_owned_asset_or_404(owner=request.user, asset_id=asset_id)
        if str(asset.submission_id) != str(submission_id):
            raise Http404
        file_obj = get_asset_stream(asset=asset, requesting_user=request.user)
        return FileResponse(
            file_obj,
            as_attachment=True,
            filename=asset.original_filename,
            content_type=asset.content_type,
        )
