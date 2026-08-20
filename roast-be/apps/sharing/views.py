from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.mixins import EnvelopeMixin
from apps.common.pagination import StandardResultsSetPagination

from .models import ShareLink
from .permissions import IsShareLinkOwner
from .selectors import (
    get_owned_roast_run_or_404,
    get_owned_share_links,
    get_share_links_for_roast,
    get_wall_of_fame_roasts,
)
from .serializers import (
    PublicRoastRunSerializer,
    ReactionCreateSerializer,
    ShareLinkListSerializer,
    ShareLinkSerializer,
    WallOfFameEntrySerializer,
)
from .services import (
    create_or_get_share_link,
    get_public_roast_payload,
    record_reaction,
    revoke_share_link,
)


@extend_schema_view(
    get=extend_schema(tags=["sharing"], responses=ShareLinkListSerializer),
    post=extend_schema(tags=["sharing"], request=None, responses=ShareLinkSerializer),
)
class ShareLinkListCreateView(EnvelopeMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/share/roasts/{roast_id}/links/ — list this roast's share
         links (active + revoked history), owner-scoped, newest first.
    POST /api/v1/share/roasts/{roast_id}/links/ — create-or-get the
         roast's active share link. No request body — the roast comes
         from the URL. 201 if a new link was created, 200 if an active
         one already existed.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    throttle_scope = "share-link-create"

    def get_throttles(self):
        # Scoped throttle only on POST (create) — GET (list) falls back
        # to the global default throttle, same pattern as
        # SubmissionRoastRunListCreateView.get_throttles.
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_roast(self):
        return get_owned_roast_run_or_404(owner=self.request.user, roast_id=self.kwargs["roast_id"])

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return ShareLink.objects.none()
        return get_share_links_for_roast(roast=self.get_roast())

    def get_serializer_class(self):
        return ShareLinkListSerializer

    def create(self, request, *args, **kwargs):
        roast = self.get_roast()  # 404s if not found/not owned
        share_link, created = create_or_get_share_link(roast=roast, requesting_user=request.user)
        out = ShareLinkSerializer(share_link, context={"request": request})
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(out.data, status=response_status)


@extend_schema_view(
    get=extend_schema(tags=["sharing"], responses=ShareLinkSerializer),
    delete=extend_schema(tags=["sharing"]),
)
class ShareLinkDetailView(EnvelopeMixin, generics.RetrieveDestroyAPIView):
    """
    GET    /api/v1/share/links/{id}/ — owner-facing detail: token,
           share_url, view_count, reaction totals, revoked_at.
    DELETE /api/v1/share/links/{id}/ — revoke (soft — sets revoked_at,
           never deletes the row or its view/reaction history).
           Idempotent: revoking an already-revoked link is a no-op 204.
    """

    permission_classes = [permissions.IsAuthenticated, IsShareLinkOwner]
    serializer_class = ShareLinkSerializer
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return ShareLink.objects.none()
        return get_owned_share_links(owner=self.request.user)

    def perform_destroy(self, instance):
        revoke_share_link(share_link=instance, requesting_user=self.request.user)


@extend_schema(tags=["sharing-public"], responses=PublicRoastRunSerializer)
class PublicSharedRoastView(EnvelopeMixin, APIView):
    """
    GET /api/v1/share/public/{token}/ — anonymous, read-only. 404s
    identically whether the token never existed, was revoked, or its
    submission was later soft-deleted — never confirms a link once
    existed. Also increments the link's view_count (see
    apps.sharing.services.get_public_roast_payload).
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "share-public-view"

    def get(self, request, token, *args, **kwargs):
        roast_run, reaction_totals = get_public_roast_payload(token=token)
        out = PublicRoastRunSerializer(roast_run, context={"reaction_totals": reaction_totals})
        return Response(out.data)


@extend_schema(tags=["sharing-public"], request=ReactionCreateSerializer)
class PublicReactionCreateView(EnvelopeMixin, APIView):
    """
    POST /api/v1/share/public/{token}/reactions/ — anonymous. Increments
    an aggregate counter only — see apps.sharing.models.Reaction's
    docstring for why there is no per-visitor dedup. Tighter throttle
    scope than the view endpoint since this is the more abuse-prone one.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "share-public-react"

    def post(self, request, token, *args, **kwargs):
        serializer = ReactionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        totals = record_reaction(
            token=token, reaction_type=serializer.validated_data["reaction_type"]
        )
        return Response(totals)


@extend_schema(tags=["sharing-public"], responses=WallOfFameEntrySerializer)
class WallOfFameListView(EnvelopeMixin, generics.ListAPIView):
    """
    GET /api/v1/share/wall-of-fame/ — anonymous, paginated feed of
    opt-in public roasts (Submission.visibility=PUBLIC), ranked by total
    reaction count by default. `?ordering=new` sorts by recency instead.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = WallOfFameEntrySerializer
    pagination_class = StandardResultsSetPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "wall-of-fame-list"

    def get_queryset(self):
        return get_wall_of_fame_roasts(ordering=self.request.query_params.get("ordering", "top"))
