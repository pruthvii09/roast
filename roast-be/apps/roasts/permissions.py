from rest_framework import permissions


class IsRoastRunOwner(permissions.BasePermission):
    """
    Defense-in-depth object-level check — the primary mechanism is
    queryset scoping in selectors.get_owned_roast_run_or_404 (so a
    non-owner's request resolves as 404, not 403).
    """

    def has_object_permission(self, request, view, obj):
        return obj.submission.owner_id == request.user.id
