from rest_framework_simplejwt.authentication import JWTAuthentication


class TokenUser:
    """User object từ JWT claim — không tra DB (cùng pattern với product-service)."""

    is_anonymous = False
    is_authenticated = True

    def __init__(self, payload: dict):
        self.id = payload.get('user_id')
        self.username = payload.get('username', '')
        self.role = payload.get('role', 'customer')
        self.full_name = payload.get('full_name', '')
        self.is_active = True
        self.is_staff = self.role in ('admin', 'staff')
        self.is_superuser = self.role == 'admin'

    def __str__(self):
        return self.username


class RemoteUserJWTAuthentication(JWTAuthentication):
    """Validate JWT của user-service, tạo TokenUser từ claims — không tra DB."""

    def get_user(self, validated_token):
        return TokenUser(validated_token)
