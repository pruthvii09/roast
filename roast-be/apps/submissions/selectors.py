from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.accounts.models import User

from .models import Submission, SubmissionAsset


def get_owned_submissions(*, owner: User, submission_type: str | None = None) -> QuerySet:
    qs = Submission.objects.filter(owner=owner)  # default manager already excludes soft-deleted
    if submission_type:
        qs = qs.filter(submission_type=submission_type)
    return qs.order_by("-created_at")


def get_owned_submission_or_404(*, owner: User, submission_id: UUID) -> Submission:
    return get_object_or_404(Submission.objects.filter(owner=owner), pk=submission_id)


def get_owned_asset_or_404(*, owner: User, asset_id: UUID) -> SubmissionAsset:
    qs = SubmissionAsset.objects.filter(
        submission__owner=owner, submission__deleted_at__isnull=True
    )
    return get_object_or_404(qs, pk=asset_id)
