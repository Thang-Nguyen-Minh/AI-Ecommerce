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
