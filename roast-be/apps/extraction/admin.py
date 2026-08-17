from django.contrib import admin

from .models import ExtractionTask


@admin.register(ExtractionTask)
class ExtractionTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "submission", "status", "processor_name", "char_count", "created_at"]
    list_filter = ["status", "processor_name"]
    search_fields = ["id", "submission__id"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
        "submission",
        "asset",
        "status",
        "processor_name",
        "char_count",
        "error_message",
    ]

    def has_add_permission(self, request):
        # ExtractionTask rows are audit records, created only by the extraction pipeline.
        return False
