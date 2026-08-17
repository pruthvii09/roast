from rest_framework import serializers

from .models import RoastFinding, RoastIntensity, RoastLanguage, RoastRun, RoastSection


class RoastSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoastSection
        fields = ["id", "key", "title", "content", "position", "metadata", "created_at"]
        read_only_fields = fields


class RoastFindingSerializer(serializers.ModelSerializer):
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
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class RoastRunSerializer(serializers.ModelSerializer):
    """Full detail representation — includes nested sections/findings."""

    sections = RoastSectionSerializer(many=True, read_only=True)
    findings = RoastFindingSerializer(many=True, read_only=True)

    class Meta:
        model = RoastRun
        fields = [
            "id",
            "submission",
            "language",
            "intensity",
            "status",
            "engine_version",
            "started_at",
            "completed_at",
            "error_message",
            "summary",
            "final_verdict",
            "score",
            "created_at",
            "updated_at",
            "sections",
            "findings",
        ]
        read_only_fields = fields


class RoastRunListSerializer(serializers.ModelSerializer):
    """Lighter representation for listing a submission's roast runs."""

    class Meta:
        model = RoastRun
        fields = [
            "id",
            "submission",
            "language",
            "intensity",
            "status",
            "engine_version",
            "started_at",
            "completed_at",
            "error_message",
            "summary",
            "score",
            "created_at",
        ]
        read_only_fields = fields


class RoastRunStatusSerializer(serializers.ModelSerializer):
    """
    Minimal payload purpose-built for GET /api/v1/roasts/{id}/status/
    polling — no nested sections/findings, so repeated polling stays
    cheap.
    """

    class Meta:
        model = RoastRun
        fields = ["id", "status", "started_at", "completed_at", "error_message"]
        read_only_fields = fields


class RoastRunCreateSerializer(serializers.Serializer):
    """
    Only language/intensity come from the request body — the submission
    comes from the URL (/submissions/{submission_id}/roasts/) and is
    resolved (with ownership/status validation) by the view before this
    serializer is ever used. ChoiceField enforces "supported
    language"/"supported intensity" directly.
    """

    language = serializers.ChoiceField(choices=RoastLanguage.choices)
    intensity = serializers.ChoiceField(choices=RoastIntensity.choices)


class RoastQuotaSerializer(serializers.Serializer):
    """
    Not model-backed — apps.roasts.services.get_roast_quota_status()
    computes this from RoastRun rows in the current window. Lets a
    client show "2 of 3 roasts left this week" ahead of hitting a 429.
    """

    limit = serializers.IntegerField()
    used = serializers.IntegerField()
    remaining = serializers.IntegerField()
    resets_at = serializers.DateTimeField(allow_null=True)
