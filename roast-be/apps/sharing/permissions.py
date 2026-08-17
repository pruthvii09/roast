from rest_framework import permissions


class IsShareLinkOwner(permissions.BasePermission):
    """
    Defense-in-depth — the primary mechanism is queryset scoping in
    selectors.get_owned_share_link_or_404. Checks the join through
    `roast.owner_id` rather than the denormalized `owner` field on
    ShareLink itself, mirroring apps.roasts.permissions.IsRoastRunOwner.
    """

    def has_object_permission(self, request, view, obj):
        return obj.roast.owner_id == request.user.id
