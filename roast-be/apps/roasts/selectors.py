from django.db.models import QuerySet

from .models import RoastRun


def get_roast_runs_for_submission(*, submission) -> QuerySet:
    return RoastRun.objects.filter(submission=submission).order_by("-created_at")


def get_owned_roast_runs(*, owner) -> QuerySet:
    return RoastRun.objects.filter(
        submission__owner=owner, submission__deleted_at__isnull=True
    ).order_by("-created_at")
