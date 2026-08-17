from apps.common.permissions import IsOwner


class IsSubmissionOwner(IsOwner):
    owner_field = "owner"
