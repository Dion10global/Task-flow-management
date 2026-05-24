from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with Admin role."""
    message = "You must be an Admin to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAdminOrReadOnly(BasePermission):
    """Admins get full access; authenticated members get read-only."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.is_admin


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner or admin can write; others read-only."""
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.user.is_admin:
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "assigned_to", None) or getattr(obj, "created_by", None)
        return owner == request.user
