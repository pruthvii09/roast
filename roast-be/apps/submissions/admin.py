from django.contrib import admin

from .models import Submission, SubmissionAsset


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "owner",
        "submission_type",
        "status",
        "visibility",
        "deleted_at",
        "created_at",
    ]
    list_filter = ["submission_type", "status", "visibility"]
    search_fields = ["id", "owner__email", "source_url", "title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def get_queryset(self, request):
        # Use the unfiltered manager so soft-deleted submissions remain
        # inspectable by staff.
        return Submission.all_objects.all()


@admin.register(SubmissionAsset)
class SubmissionAssetAdmin(admin.ModelAdmin):
    list_display = ["id", "submission", "original_filename", "content_type", "size_bytes"]
    search_fields = ["id", "original_filename", "submission__id"]
    readonly_fields = ["id", "created_at", "updated_at", "checksum"]
