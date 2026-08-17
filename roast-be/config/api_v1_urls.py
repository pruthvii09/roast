from django.urls import include, path

urlpatterns = [
    path("health/", include("apps.common.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("submissions/", include("apps.submissions.urls")),
    path("roasts/", include("apps.roasts.urls")),
    path("share/", include("apps.sharing.urls")),
]
