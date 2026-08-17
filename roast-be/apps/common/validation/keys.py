import uuid


def generate_storage_key(*, namespace: str, extension: str) -> str:
    """
    Returns an opaque, unguessable storage key with no user-supplied path
    components, e.g. "submissions/<uuid4>/<uuid4>.pdf".

    `namespace` must be a fixed, server-side literal (e.g. "submissions"),
    never a client-controlled value. `extension` must already be
    normalized/validated (see validate_extension) — this function does not
    re-validate it, it only appends it.
    """
    return f"{namespace}/{uuid.uuid4()}/{uuid.uuid4()}{extension}"
