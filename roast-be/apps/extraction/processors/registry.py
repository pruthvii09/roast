from django.conf import settings

from apps.extraction.exceptions import UnsupportedContentTypeError
from apps.submissions.models import SubmissionType

from .base import SubmissionProcessor
from .github import GitHubProcessor
from .resume import ResumeProcessor
from .website import WebsiteProcessor

# Settings-driven factory (mirrors apps.common.storage.get_storage() and
# apps.ai.providers.get_ai_provider()): swapping/adding a processor is
# one new SubmissionProcessor subclass + one new entry here — no changes
# anywhere that calls get_processor(). GitHubProcessor is the one
# processor that takes a constructor argument today (an optional access
# token) — this is also where a future per-user OAuth token would get
# threaded in, instead of the current global settings-based default.
_PROCESSOR_FACTORIES = {
    SubmissionType.RESUME: lambda: ResumeProcessor(),
    SubmissionType.WEBSITE: lambda: WebsiteProcessor(),
    SubmissionType.GITHUB: lambda: GitHubProcessor(
        access_token=settings.EXTRACTION_GITHUB_ACCESS_TOKEN or None
    ),
}


def get_processor(submission) -> SubmissionProcessor:
    factory = _PROCESSOR_FACTORIES.get(submission.submission_type)
    if factory is None:
        raise UnsupportedContentTypeError(
            f"No processor available yet for submission type {submission.submission_type!r}."
        )
    return factory()
