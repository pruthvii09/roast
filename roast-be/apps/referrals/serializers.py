from django.conf import settings
from rest_framework import serializers


class ReferralInfoSerializer(serializers.Serializer):
    """
    GET /api/v1/referrals/me/ payload. Not model-backed — assembled by
    the view from ReferralCode + apps.referrals.selectors.get_referral_stats.
    """

    code = serializers.CharField()
    referral_url = serializers.SerializerMethodField()
    total_referred = serializers.IntegerField()
    total_qualified = serializers.IntegerField()

    def get_referral_url(self, obj):
        return f"{settings.FRONTEND_SHARE_BASE_URL}/register?ref={obj['code']}"
