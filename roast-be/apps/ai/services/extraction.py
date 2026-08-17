from ..exceptions import SubmissionExtractionError


def ensure_extracted_text(submission) -> str:
    """
    The "load submission" step of the roast pipeline. All submission
    processing (resume/website/GitHub) is owned entirely by
    apps.extraction now — queued asynchronously at submission-creation
    time (see apps.submissions.services.create_submission) and routed by
    apps.extraction.processors.get_processor. By the time a roast run
    can even be created,
    apps.roasts.services._validate_submission_is_roastable already
    required the submission to be `ready`, which apps.extraction only
    sets alongside a populated `extracted_text` — so reaching this
    function with empty extracted_text means something is internally
    inconsistent (e.g. a race), not a normal, user-facing failure.
    Raising here rather than processing anything keeps apps.ai free of
    any submission-type-specific processing logic.
    """
    if not submission.extracted_text:
        raise SubmissionExtractionError("Submission has no extracted text available yet.")
    return submission.extracted_text
