from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.roasts.views import SubmissionRoastRunListCreateView

from .views import AssetDownloadView, SubmissionStatusView, SubmissionViewSet

router = DefaultRouter()
router.register(r"", SubmissionViewSet, basename="submission")

urlpatterns = [
    path(
        "<uuid:submission_id>/assets/<uuid:asset_id>/download/",
        AssetDownloadView.as_view(),
        name="submission-asset-download",
    ),
    path(
        "<uuid:submission_id>/status/",
        SubmissionStatusView.as_view(),
        name="submission-status",
    ),
    path(
        "<uuid:submission_id>/roasts/",
        SubmissionRoastRunListCreateView.as_view(),
        name="submission-roasts",
    ),
    *router.urls,
]
