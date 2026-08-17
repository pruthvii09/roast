import abc
from dataclasses import dataclass, field


@dataclass
class ProcessingResult:
    """
    A processor's output: normalized plain text (stored on
    Submission.extracted_text) plus optional structured extras (stored
    on Submission.metadata, an existing JSONField no processor
    previously populated) — e.g. a GitHub repo's stars/language/topics,
    or a website's content type. `metadata` defaults to empty; most
    processors don't need it.
    """

    text: str
    metadata: dict = field(default_factory=dict)


class SubmissionProcessor(abc.ABC):
    """
    Source-agnostic interface for turning a Submission's material into
    plain text: SubmissionProcessor -> ResumeProcessor / WebsiteProcessor
    / GitHubProcessor (see apps.extraction.processors.registry.get_processor
    for how a submission is routed to the right one).

    Deliberately takes the whole `submission`, not a file object or a
    URL string: a file-based processor (ResumeProcessor) pulls its bytes
    from `submission.assets`, while a URL-based processor (Website/GitHub)
    pulls `submission.source_url` — neither shape is privileged by this
    interface, so neither needed to change when GitHub/website support
    was added on top of phase 5's resume-only version.

    Raises an apps.extraction.exceptions.ExtractionError subclass on any
    failure (unsupported/corrupt/empty/invalid URL/remote fetch failed)
    — never returns an empty result or None as a way of signaling
    failure.
    """

    #: Short machine-readable name recorded on ExtractionTask.processor_name.
    processor_name: str = "unknown"

    @abc.abstractmethod
    def process(self, submission) -> ProcessingResult:
        """Return a ProcessingResult with non-empty text, or raise ExtractionError."""
