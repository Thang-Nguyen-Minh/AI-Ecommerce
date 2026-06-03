from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication


class TokenUser:
    is_anonymous = False
    is_authenticated = True

    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.username = payload.get('username', '')
        self.role = payload.get('role', 'customer')
        self.is_active = True
        self.is_staff = self.role in ('admin', 'staff')
        self.is_superuser = self.role == 'admin'


class RemoteUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        return TokenUser(validated_token)


class IsAdminOrStaff(BasePermission):
    """BR-5: chỉ staff/admin được cập nhật trạng thái giao hàng."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) in ('admin', 'staff'))
