from django.contrib import admin

from .models import Referral, ReferralCode


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "code", "created_at"]
    search_fields = ["id", "code", "owner__email"]
    readonly_fields = ["id", "code", "created_at", "updated_at"]


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "referrer",
        "referred",
        "qualified_at",
        "referrer_bonus_granted",
        "created_at",
    ]
    list_filter = ["referrer_bonus_granted", "qualified_at"]
    search_fields = ["id", "code", "referrer__email", "referred__email"]
    readonly_fields = ["id", "code", "created_at", "updated_at"]
