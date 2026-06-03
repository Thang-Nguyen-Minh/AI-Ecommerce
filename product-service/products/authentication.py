from rest_framework_simplejwt.authentication import JWTAuthentication


class TokenUser:
    """User object xây dựng từ JWT claim — không cần DB lookup."""

    is_anonymous = False
    is_authenticated = True

    def __init__(self, payload: dict):
        self.id = payload.get("user_id")
        self.username = payload.get("username", "")
        self.role = payload.get("role", "customer")
        self.full_name = payload.get("full_name", "")
        self.is_active = True
        self.is_staff = self.role in ("admin", "staff")
        self.is_superuser = self.role == "admin"

    def __str__(self):
        return self.username


class RemoteUserJWTAuthentication(JWTAuthentication):
    """
    Xác thực JWT do user-service cấp mà không tra cứu DB.
    Dùng chung SECRET_KEY với user-service → chữ ký hợp lệ.
    Claim `role` được ghi vào request.user để permission đọc.
    """

    def get_user(self, validated_token):
        return TokenUser(validated_token)
