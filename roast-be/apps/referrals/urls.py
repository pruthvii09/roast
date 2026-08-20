from django.urls import path

from .views import ReferralInfoView

urlpatterns = [
    path("me/", ReferralInfoView.as_view(), name="referral-me"),
]
