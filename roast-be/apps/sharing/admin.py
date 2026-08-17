from django.contrib import admin

from .models import Reaction, ShareLink


class ReactionInline(admin.TabularInline):
    model = Reaction
    extra = 0
    readonly_fields = ["id", "reaction_type", "count", "created_at", "updated_at"]


@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "roast", "owner", "token", "view_count", "revoked_at", "created_at"]
    list_filter = ["revoked_at"]
    search_fields = ["id", "token", "roast__id", "owner__email"]
    readonly_fields = ["id", "token", "created_at", "updated_at", "view_count"]
    inlines = [ReactionInline]
