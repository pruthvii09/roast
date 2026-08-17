from django.conf import settings
from rest_framework import serializers

from apps.roasts.models import RoastFinding, RoastRun, RoastSection
from apps.submissions.models import Submission

from .models import ReactionType, ShareLink
from .services import get_reaction_totals

# --- Owner-facing (authenticated management) --------------------------------


class ShareLinkSerializer(serializers.ModelSerializer):
    """Full detail — used for create/detail responses."""

    share_url = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = ShareLink
        fields = [
            "id",
            "token",
            "share_url",
            "is_active",
            "view_count",
            "reactions",
            "revoked_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_share_url(self, obj):
        return f"{settings.FRONTEND_SHARE_BASE_URL}/r/{obj.token}"

    def get_is_active(self, obj):
        return obj.revoked_at is None

    def get_reactions(self, obj):
        return get_reaction_totals(share_link=obj)


class ShareLinkListSerializer(serializers.ModelSerializer):
    """Lighter representation for the list endpoint — omits the extra reactions query per row."""

    share_url = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = ShareLink
        fields = ["id", "token", "share_url", "is_active", "view_count", "revoked_at", "created_at"]
        read_only_fields = fields

    def get_share_url(self, obj):
        return f"{settings.FRONTEND_SHARE_BASE_URL}/r/{obj.token}"

    def get_is_active(self, obj):
        return obj.revoked_at is None


# --- Public-facing (anonymous) -----------------------------------------------
# New, deliberately narrow serializers — never reuse apps.roasts/apps.submissions'
# owner-scoped serializers here. See apps.submissions.serializers.SubmissionSerializer's
# docstring: a public view "must build its own explicit serializer ... so it
# can't accidentally leak extracted_text". Same reasoning applies to source_url,
# metadata, and any owner/email field.


class PublicSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["submission_type", "title"]
        read_only_fields = fields


class PublicRoastSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoastSection
        # `id` is included (unlike the plan's original field list) so the
        # frontend can reuse RoastSections/FindingsList's existing
        # key={x.id} props unmodified — a child row's own UUID carries no
        # PII/ownership signal.
        fields = ["id", "key", "title", "content", "position"]
        read_only_fields = fields


class PublicRoastFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoastFinding
        fields = [
            "id",
            "category",
            "severity",
            "title",
            "roast_text",
            "actual_feedback",
            "position",
        ]
        read_only_fields = fields


class PublicRoastRunSerializer(serializers.ModelSerializer):
    """
    GET /api/v1/share/public/{token}/ payload. Deliberately excludes
    `id` (the roast's own UUID never needs to leak into a public
    response — the share token is the only externally meaningful
    identifier), `owner`, `engine_version`, and `error_message`.
    """

    submission = PublicSubmissionSerializer(read_only=True)
    sections = PublicRoastSectionSerializer(many=True, read_only=True)
    findings = PublicRoastFindingSerializer(many=True, read_only=True)
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = RoastRun
        fields = [
            "language",
            "intensity",
            "status",
            "summary",
            "final_verdict",
            "score",
            "created_at",
            "submission",
            "sections",
            "findings",
            "reactions",
        ]
        read_only_fields = fields

    def get_reactions(self, obj):
        return self.context.get("reaction_totals", {})


class ReactionCreateSerializer(serializers.Serializer):
    reaction_type = serializers.ChoiceField(choices=ReactionType.choices)
