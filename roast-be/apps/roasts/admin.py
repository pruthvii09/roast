from django.contrib import admin

from .models import RoastFinding, RoastRun, RoastSection


class RoastSectionInline(admin.TabularInline):
    model = RoastSection
    extra = 0
    readonly_fields = ["id", "created_at", "updated_at"]


class RoastFindingInline(admin.TabularInline):
    model = RoastFinding
    extra = 0
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(RoastRun)
class RoastRunAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "submission",
        "owner",
        "language",
        "intensity",
        "status",
        "score",
        "engine_version",
        "created_at",
    ]
    list_filter = ["language", "intensity", "status"]
    search_fields = ["id", "submission__id", "owner__email"]
    readonly_fields = ["id", "created_at", "updated_at", "started_at", "completed_at"]
    inlines = [RoastSectionInline, RoastFindingInline]


@admin.register(RoastSection)
class RoastSectionAdmin(admin.ModelAdmin):
    list_display = ["id", "roast", "key", "title", "position"]
    search_fields = ["id", "key", "roast__id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(RoastFinding)
class RoastFindingAdmin(admin.ModelAdmin):
    list_display = ["id", "roast", "category", "severity", "title", "position"]
    list_filter = ["severity"]
    search_fields = ["id", "category", "roast__id"]
    readonly_fields = ["id", "created_at", "updated_at"]
