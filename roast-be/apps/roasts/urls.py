from django.urls import path

from .views import RoastQuotaView, RoastRunDetailView, RoastRunStatusView

urlpatterns = [
    # Listed before <uuid:id>/ defensively (not strictly required — "quota"
    # never matches the uuid converter — but keeps intent obvious).
    path("quota/", RoastQuotaView.as_view(), name="roast-quota"),
    path("<uuid:id>/status/", RoastRunStatusView.as_view(), name="roast-status"),
    path("<uuid:id>/", RoastRunDetailView.as_view(), name="roast-detail"),
]
