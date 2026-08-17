from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Generic object-level permission: the object must have an `owner`
    attribute matching request.user.

    This is defense-in-depth, not the primary access-control mechanism —
    views should already scope their queryset to `owner=request.user` so
    DRF's `get_object()` never finds another user's row in the first
    place (surfacing as 404, not 403, so we never confirm the existence
    of another user's resource via status code).
    """

    owner_field = "owner"

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, self.owner_field, None)
        return owner is not None and owner == request.user
