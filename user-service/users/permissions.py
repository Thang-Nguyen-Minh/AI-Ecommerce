from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Chỉ Admin được phép"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsAdminOrStaff(BasePermission):
    """Admin hoặc Staff được phép"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('admin', 'staff')
        )


class IsOwnerOrAdmin(BasePermission):
    """Chủ tài khoản hoặc Admin"""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.role == 'admin'
        return obj == request.user or request.user.role == 'admin'