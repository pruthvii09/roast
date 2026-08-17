import pytest

from apps.submissions.serializers import SubmissionCreateSerializer

pytestmark = pytest.mark.django_db


def _valid(**overrides):
    data = {"submission_type": "website", "source_url": "https://example.com"}
    data.update(overrides)
    return data


class TestSubmissionCreateSerializerValidation:
    def test_resume_with_file_is_valid(self, valid_resume_file):
        serializer = SubmissionCreateSerializer(
            data={"submission_type": "resume", "file": valid_resume_file}
        )
        assert serializer.is_valid(), serializer.errors

    def test_resume_with_url_instead_of_file_is_invalid(self):
        serializer = SubmissionCreateSerializer(
            data={"submission_type": "resume", "source_url": "https://example.com"}
        )
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_website_with_url_is_valid(self):
        serializer = SubmissionCreateSerializer(data=_valid(submission_type="website"))
        assert serializer.is_valid(), serializer.errors

    def test_website_with_file_instead_of_url_is_invalid(self, valid_resume_file):
        serializer = SubmissionCreateSerializer(
            data={"submission_type": "website", "file": valid_resume_file}
        )
        assert not serializer.is_valid()
        assert "source_url" in serializer.errors

    def test_github_with_non_github_url_is_invalid(self):
        serializer = SubmissionCreateSerializer(
            data={"submission_type": "github", "source_url": "https://notgithub.com/octocat"}
        )
        assert not serializer.is_valid()
        assert "source_url" in serializer.errors

    def test_github_with_github_url_is_valid(self):
        serializer = SubmissionCreateSerializer(
            data={"submission_type": "github", "source_url": "https://github.com/octocat"}
        )
        assert serializer.is_valid(), serializer.errors
