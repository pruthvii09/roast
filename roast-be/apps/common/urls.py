from django.urls import path

from .views import LivenessView, ReadinessView

urlpatterns = [
    path("", LivenessView.as_view(), name="health-liveness"),
    path("ready/", ReadinessView.as_view(), name="health-readiness"),
]
