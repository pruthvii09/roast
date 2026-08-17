from django.contrib import admin

from .models import AIRequest, PromptVersion


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "language", "version", "is_active", "created_at"]
    list_filter = ["name", "language", "is_active"]
    search_fields = ["id", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "roast",
        "provider",
        "model",
        "success",
        "input_tokens",
        "output_tokens",
        "cost",
        "latency_ms",
        "created_at",
    ]
    list_filter = ["provider", "success"]
    search_fields = ["id", "roast__id"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "roast",
        "provider",
        "model",
        "prompt_version",
        "input_tokens",
        "output_tokens",
        "latency_ms",
        "cost",
        "success",
        "error",
    ]

    def has_add_permission(self, request):
        return False  # AIRequest rows are audit records, created only by the roasting service
