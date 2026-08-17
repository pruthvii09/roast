from urllib.parse import urlparse

from rest_framework import serializers

from .models import Submission, SubmissionAsset, SubmissionType, SubmissionVisibility
from .services import create_submission, update_submission

_GITHUB_HOSTS = {"github.com", "www.github.com"}


class SubmissionAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAsset
        fields = ["id", "original_filename", "content_type", "size_bytes", "created_at"]
        read_only_fields = fields


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Full detail representation, returned to the owner on create/retrieve/
    update. Includes `extracted_text` and `metadata` — safe here because
    every endpoint that uses this serializer is owner-scoped (see
    SubmissionViewSet.get_queryset). There is no public-facing endpoint
    yet; a future public/shared-roast view (the sharing app) must build
    its own explicit serializer rather than reusing this one, so it can't
    accidentally leak extracted_text.
    """

    assets = SubmissionAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "submission_type",
            "title",
            "status",
            "error_message",
            "visibility",
            "source_url",
            "extracted_text",
            "metadata",
            "created_at",
            "updated_at",
            "assets",
        ]
        read_only_fields = fields


class SubmissionListSerializer(serializers.ModelSerializer):
    """
    Lighter representation for the list endpoint — omits `extracted_text`
    and `metadata`, which can be large and aren't needed to render a
    list view.
    """

    assets = SubmissionAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "submission_type",
            "title",
            "status",
            "error_message",
            "visibility",
            "source_url",
            "created_at",
            "updated_at",
            "assets",
        ]
        read_only_fields = fields


class SubmissionStatusSerializer(serializers.ModelSerializer):
    """
    Minimal payload purpose-built for GET /api/v1/submissions/{id}/status/
    polling while extraction runs in the background — mirrors
    apps.roasts.serializers.RoastRunStatusSerializer.
    """

    class Meta:
        model = Submission
        fields = ["id", "status", "error_message", "created_at", "updated_at"]
        read_only_fields = fields


class SubmissionCreateSerializer(serializers.Serializer):
    submission_type = serializers.ChoiceField(choices=SubmissionType.choices)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    visibility = serializers.ChoiceField(
        choices=SubmissionVisibility.choices,
        required=False,
        default=SubmissionVisibility.PRIVATE,
    )
    source_url = serializers.URLField(max_length=2048, required=False)
    file = serializers.FileField(required=False, write_only=True)

    def validate(self, attrs):
        submission_type = attrs.get("submission_type")
        uploaded_file = attrs.get("file")
        source_url = attrs.get("source_url")

        if submission_type == SubmissionType.RESUME:
            if not uploaded_file:
                raise serializers.ValidationError(
                    {"file": "A file is required for resume submissions."}
                )
            if source_url:
                raise serializers.ValidationError(
                    {"source_url": "source_url must not be set for resume submissions."}
                )
        elif submission_type in (SubmissionType.WEBSITE, SubmissionType.GITHUB):
            if not source_url:
                raise serializers.ValidationError(
                    {"source_url": "source_url is required for this submission type."}
                )
            if uploaded_file:
                raise serializers.ValidationError(
                    {"file": "file must not be set for URL-based submission types."}
                )
            if submission_type == SubmissionType.GITHUB:
                if urlparse(source_url).netloc.lower() not in _GITHUB_HOSTS:
                    raise serializers.ValidationError(
                        {"source_url": "GitHub submissions must be a github.com URL."}
                    )

        return attrs

    def create(self, validated_data):
        result = create_submission(
            owner=self.context["request"].user,
            submission_type=validated_data["submission_type"],
            uploaded_file=validated_data.get("file"),
            source_url=validated_data.get("source_url"),
            title=validated_data.get("title", ""),
            visibility=validated_data.get("visibility", SubmissionVisibility.PRIVATE),
        )
        return result.submission


class SubmissionUpdateSerializer(serializers.Serializer):
    """
    Partial-update-only surface: `title` and `visibility` are the only
    user-mutable fields post-creation. `submission_type`/`source_url` are
    immutable (they underpin the CHECK constraint and any assets already
    tied to the original type); `status` is system-managed by the future
    processing pipeline, not user-settable via PATCH.
    """

    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    visibility = serializers.ChoiceField(choices=SubmissionVisibility.choices, required=False)

    def update(self, instance, validated_data):
        return update_submission(submission=instance, **validated_data)
