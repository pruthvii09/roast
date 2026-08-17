import pytest
from django.db import IntegrityError, transaction

from apps.submissions.models import Submission, SubmissionType
from apps.submissions.tests.factories import SubmissionFactory

pytestmark = pytest.mark.django_db


def test_website_without_source_url_violates_check_constraint(user):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Submission.objects.create(
                owner=user, submission_type=SubmissionType.WEBSITE, source_url=None
            )


def test_github_without_source_url_violates_check_constraint(user):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Submission.objects.create(
                owner=user, submission_type=SubmissionType.GITHUB, source_url=None
            )


def test_resume_without_source_url_is_allowed(user):
    submission = Submission.objects.create(
        owner=user, submission_type=SubmissionType.RESUME, source_url=None
    )
    assert submission.pk is not None


def test_soft_delete_hides_from_default_manager():
    submission = SubmissionFactory()
    submission.soft_delete()

    assert not Submission.objects.filter(pk=submission.pk).exists()
    assert Submission.all_objects.filter(pk=submission.pk).exists()
    revived = Submission.all_objects.get(pk=submission.pk)
    assert revived.deleted_at is not None
