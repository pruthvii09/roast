from django.urls import path

from .views import (
    PublicReactionCreateView,
    PublicSharedRoastView,
    ShareLinkDetailView,
    ShareLinkListCreateView,
)

urlpatterns = [
    path(
        "roasts/<uuid:roast_id>/links/",
        ShareLinkListCreateView.as_view(),
        name="share-link-list-create",
    ),
    path("links/<uuid:id>/", ShareLinkDetailView.as_view(), name="share-link-detail"),
    path("public/<str:token>/", PublicSharedRoastView.as_view(), name="share-public-roast"),
    path(
        "public/<str:token>/reactions/",
        PublicReactionCreateView.as_view(),
        name="share-public-reaction",
    ),
]
