import hashlib
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.common.storage import get_storage
from apps.common.validation.files import validate_file_size, validate_file_type
from apps.common.validation.keys import generate_storage_key
from apps.extraction.services import dispatch_extraction_processing, queue_extraction

from .models import (
    Submission,
    SubmissionAsset,
    SubmissionStatus,
    SubmissionType,
    SubmissionVisibility,
)


@dataclass
class CreateSubmissionResult:
    submission: Submission
    asset: SubmissionAsset | None


def _compute_checksum(file_obj) -> str:
    file_obj.seek(0)
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(64 * 1024), b""):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def create_submission(
    *,
    owner: User,
    submission_type: str,
    uploaded_file=None,
    source_url: str | None = None,
    title: str = "",
    visibility: str = SubmissionVisibility.PRIVATE,
) -> CreateSubmissionResult:
    """
    Validates type-specific invariants (redundant with serializer
    validation as a defensive safety net — this function must not assume
    it's only ever called from a validated serializer), then persists the
    Submission (+ SubmissionAsset for resumes). `status` is left at its
    model default (`processing`). Every submission type queues an
    ExtractionTask in the same transaction that creates its rows and
    dispatches it to Celery on commit (see apps.extraction.services) —
    that task (not this function) is what later transitions the
    submission to `ready`/`failed`, via
    apps.extraction.processors.get_processor's submission_type-keyed
    routing.

    The file is written to storage *before* the DB transaction opens, to
    avoid holding a Postgres transaction open across a potentially slow
    disk write. Accepted risk: if the DB commit fails after a successful
    storage write, the file is orphaned. No cleanup job exists for this
    yet (would be a cheap future Celery periodic task once Celery beat
    exists).
    """
    if submission_type == SubmissionType.RESUME:
        if not uploaded_file:
            raise ValueError("A file is required for resume submissions.")
        if source_url:
            raise ValueError("source_url must not be set for resume submissions.")

        validate_file_size(uploaded_file, settings.MAX_UPLOAD_SIZE_BYTES)
        content_type, extension = validate_file_type(
            uploaded_file,
            allowed_content_types=settings.ALLOWED_RESUME_CONTENT_TYPES,
            allowed_extensions=settings.ALLOWED_RESUME_EXTENSIONS,
            filename=uploaded_file.name,
        )
        checksum = _compute_checksum(uploaded_file)
        storage_key = generate_storage_key(namespace="submissions", extension=extension)
        get_storage().save(storage_key, uploaded_file)

        with transaction.atomic():
            submission = Submission.objects.create(
                owner=owner,
                submission_type=submission_type,
                source_url=None,
                title=title,
                visibility=visibility,
            )
            asset = SubmissionAsset.objects.create(
                submission=submission,
                storage_key=storage_key,
                original_filename=uploaded_file.name,
                content_type=content_type,
                size_bytes=uploaded_file.size,
                checksum=checksum,
            )
            # Queued in the same transaction as the Submission/Asset rows
            # so the extraction task can never exist without its owning
            # rows (or vice versa). Dispatched only after commit — see
            # below and apps.roasts.services.create_roast_run for the
            # identical create-then-on_commit-dispatch split.
            extraction_task = queue_extraction(submission=submission, asset=asset)

    elif submission_type in (SubmissionType.WEBSITE, SubmissionType.GITHUB):
        if not source_url:
            raise ValueError("source_url is required for this submission type.")
        if uploaded_file:
            raise ValueError("file must not be set for URL-based submission types.")

        with transaction.atomic():
            submission = Submission.objects.create(
                owner=owner,
                submission_type=submission_type,
                source_url=source_url,
                title=title,
                visibility=visibility,
            )
            asset = None
            extraction_task = queue_extraction(submission=submission, asset=None)

    else:
        raise ValueError(f"Unsupported submission_type: {submission_type!r}")

    # One shared dispatch path for every submission type — extraction
    # processing is a single domain abstraction regardless of source
    # (see apps.extraction.processors), not something special-cased
    # per type at the call site.
    transaction.on_commit(lambda: dispatch_extraction_processing(extraction_task.id))
    return CreateSubmissionResult(submission=submission, asset=asset)


def update_submission(*, submission: Submission, **fields) -> Submission:
    """
    Applies a partial update of user-mutable presentation fields only
    (title, visibility). Source-material fields (submission_type,
    source_url) are immutable after creation — changing them would
    invalidate the CHECK constraint's premise and any assets already
    tied to the original type. `status` is not user-settable here either
    — it's system-managed by the (future) processing pipeline.
    """
    allowed = {"title", "visibility"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Cannot update field(s): {sorted(unknown)}")

    for field, value in fields.items():
        setattr(submission, field, value)
    submission.save(update_fields=list(fields))
    return submission


def delete_submission(*, submission: Submission, requesting_user: User) -> None:
    """
    Ownership is expected to already be enforced by the view/permission
    layer; this defensively re-checks it. Sequence, inside one
    transaction:
      1. Purge each asset's storage bytes (idempotent hard delete).
      2. Hard-delete the asset rows.
      3. Soft-delete the submission (sets deleted_at) and mark its
         status `deleted` — set together rather than via the generic
         SoftDeleteModel.soft_delete() helper, since Submission has this
         extra status dimension to keep in sync.
    If a storage.delete() call raises, the whole transaction rolls back
    at the DB level — but a storage delete that partially succeeds
    across multiple assets is NOT rolled back at the filesystem level
    (inherent limitation of mixing filesystem side effects with DB
    transactions). Accepted risk for the local backend, given
    storage.delete is a simple, low-failure-rate local unlink.
    """
    if submission.owner_id != requesting_user.id:
        raise PermissionDenied("You do not have permission to delete this submission.")

    storage = get_storage()
    with transaction.atomic():
        for asset in submission.assets.all():
            storage.delete(asset.storage_key)
            asset.delete()
        submission.status = SubmissionStatus.DELETED
        submission.deleted_at = timezone.now()
        submission.save(update_fields=["status", "deleted_at"])


def get_asset_stream(*, asset: SubmissionAsset, requesting_user: User):
    """
    Ownership check is performed by the caller/permission class. Returns
    a readable file-like object for streaming the asset's bytes back to
    an authenticated owner — never a public media URL.
    """
    if asset.submission.owner_id != requesting_user.id:
        raise PermissionDenied("You do not have permission to access this asset.")
    return get_storage().open(asset.storage_key)
