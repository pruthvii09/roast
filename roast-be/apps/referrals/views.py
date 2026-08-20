from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import EnvelopeMixin

from .selectors import get_referral_stats
from .serializers import ReferralInfoSerializer
from .services import get_or_create_referral_code


@extend_schema(tags=["referrals"], responses=ReferralInfoSerializer)
class ReferralInfoView(EnvelopeMixin, APIView):
    """
    GET /api/v1/referrals/me/ — the caller's own referral code, share
    URL, and how many people they've referred/qualified. Get-or-creates
    the code lazily (see apps.referrals.services.get_or_create_referral_code)
    rather than at registration time, so every user has exactly one
    stable code without needing a signal on User creation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        referral_code = get_or_create_referral_code(user=request.user)
        total_referred, total_qualified = get_referral_stats(user=request.user)
        payload = {
            "code": referral_code.code,
            "total_referred": total_referred,
            "total_qualified": total_qualified,
        }
        return Response(ReferralInfoSerializer(payload).data)
