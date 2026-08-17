import pytest
from django.core.exceptions import PermissionDenied

from apps.common.exceptions import FileValidationError
from apps.common.storage import get_storage
from apps.submissions.models import Submission, SubmissionAsset, SubmissionType
from apps.submissions.services import create_submission, delete_submission
from apps.submissions.tests.factories import SubmissionFactory

pytestmark = pytest.mark.django_db


class TestCreateSubmission:
    def test_resume_happy_path(self, user, valid_resume_file):
        result = create_submission(
            owner=user, submission_type=SubmissionType.RESUME, uploaded_file=valid_resume_file
        )
        assert result.submission.submission_type == SubmissionType.RESUME
        assert result.asset is not None
        assert result.asset.content_type == "application/pdf"
        assert get_storage().exists(result.asset.storage_key)

    def test_website_happy_path(self, user):
        result = create_submission(
            owner=user,
            submission_type=SubmissionType.WEBSITE,
            source_url="https://example.com/me",
        )
        assert result.submission.source_url == "https://example.com/me"
        assert result.asset is None

    def test_github_happy_path(self, user):
        result = create_submission(
            owner=user,
            submission_type=SubmissionType.GITHUB,
            source_url="https://github.com/octocat",
        )
        assert result.submission.submission_type == SubmissionType.GITHUB
        assert result.asset is None

    def test_resume_without_file_raises(self, user):
        with pytest.raises(ValueError):
            create_submission(owner=user, submission_type=SubmissionType.RESUME)

    def test_resume_oversized_file_raises(self, user, oversized_resume_file):
        with pytest.raises(FileValidationError):
            create_submission(
                owner=user,
                submission_type=SubmissionType.RESUME,
                uploaded_file=oversized_resume_file,
            )

    def test_resume_spoofed_mime_raises(self, user, spoofed_resume_file):
        with pytest.raises(FileValidationError):
            create_submission(
                owner=user,
                submission_type=SubmissionType.RESUME,
                uploaded_file=spoofed_resume_file,
            )

    def test_website_without_url_raises(self, user):
        with pytest.raises(ValueError):
            create_submission(owner=user, submission_type=SubmissionType.WEBSITE)


class TestDeleteSubmission:
    def test_purges_storage_and_soft_deletes(self, user, valid_resume_file):
        result = create_submission(
            owner=user, submission_type=SubmissionType.RESUME, uploaded_file=valid_resume_file
        )
        storage_key = result.asset.storage_key
        storage = get_storage()
        assert storage.exists(storage_key)

        delete_submission(submission=result.submission, requesting_user=user)

        assert storage.exists(storage_key) is False
        assert not SubmissionAsset.objects.filter(pk=result.asset.pk).exists()
        assert not Submission.objects.filter(pk=result.submission.pk).exists()
        revived = Submission.all_objects.get(pk=result.submission.pk)
        assert revived.deleted_at is not None

    def test_rejects_deletion_by_non_owner(self, user, user_factory):
        submission = SubmissionFactory(owner=user)
        other_user = user_factory(email="someone-else@example.com")

        with pytest.raises(PermissionDenied):
            delete_submission(submission=submission, requesting_user=other_user)
