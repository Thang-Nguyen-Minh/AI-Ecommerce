import logging
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import UserAddress
from .permissions import IsAdmin, IsOwnerOrAdmin
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserAddressSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    AdminCreateUserSerializer,
)

logger = logging.getLogger('users')
User   = get_user_model()


# ════════════════════════════════════════
#  AUTH ENDPOINTS
# ════════════════════════════════════════

class LoginView(APIView):
    """
    POST /auth/login/
    Body: { email, password }
    Response 200: { access: JWT (với role claim), refresh: JWT, user: {...} }
    Response 401: { error: "Sai thông tin đăng nhập" }
    Response 400: { error: "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email và password là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Sai thông tin đăng nhập'}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']
        logger.info(f"[AUTH] Login success: {user.email}")

        # BR-5: dùng CustomTokenObtainPairSerializer để JWT có claim role
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserDetailSerializer(user).data,
        }, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    POST /auth/register/
    Body: { email, password, role (optional) }
    Response 201: { id, email, role }
    Response 400: { field: ["error message"] }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        logger.info(f"[AUTH] Đăng ký thành công: {user.email}")

        return Response({
            'id': user.id,
            'email': user.email,
            'role': user.role
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    POST /auth/logout/
    Body: { refresh }
    Blacklist refresh token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            logger.info(f"[AUTH] Logout: {request.user.username}")
            return Response({'message': 'Đăng xuất thành công'})
        except TokenError:
            return Response({'message': 'Đăng xuất thành công'})


class MeView(APIView):
    """
    GET  /users/me/  → Lấy thông tin user hiện tại
    PUT  /users/me/  → Cập nhật thông tin
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        logger.info(f"[USER] Cập nhật profile: {request.user.username}")
        return Response({
            'message': 'Cập nhật thành công',
            'user': UserDetailSerializer(request.user).data
        })


class ChangePasswordView(APIView):
    """
    POST /users/me/change-password/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        logger.info(f"[USER] Đổi mật khẩu: {request.user.username}")
        return Response({'message': 'Đổi mật khẩu thành công'})


# ════════════════════════════════════════
#  USER MANAGEMENT (Admin)
# ════════════════════════════════════════

class UserListView(APIView):
    """
    GET  /users/ → Admin: danh sách tất cả users
    POST /users/ → Admin: tạo tài khoản staff/admin (BR-2)
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminCreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        logger.info(f"[ADMIN] Tạo tài khoản {user.role}: {user.email} bởi {request.user.email}")
        return Response({
            'id':    user.id,
            'email': user.email,
            'role':  user.role,
        }, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """
    GET    /users/:id/   → Chi tiết user
    PUT    /users/:id/   → Cập nhật (Admin)
    DELETE /users/:id/   → Vô hiệu hóa (Admin)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Không tìm thấy user'}, status=404)
        # Chỉ admin xem toàn bộ; user thường chỉ xem được chính mình
        if not (request.user.role == 'admin' or request.user.pk == user.pk):
            return Response({'error': 'Không có quyền'}, status=403)
        return Response(UserDetailSerializer(user).data)

    def put(self, request, pk):
        if request.user.role != 'admin':
            return Response({'error': 'Chỉ Admin mới có quyền'}, status=403)
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Không tìm thấy user'}, status=404)

        # Admin có thể đổi role
        allowed_fields = ['full_name', 'phone', 'role', 'is_active', 'avatar']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        for key, val in data.items():
            setattr(user, key, val)
        user.save()
        return Response(UserDetailSerializer(user).data)

    def delete(self, request, pk):
        if request.user.role != 'admin':
            return Response({'error': 'Chỉ Admin mới có quyền'}, status=403)
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Không tìm thấy user'}, status=404)
        if user == request.user:
            return Response({'error': 'Không thể vô hiệu hóa chính mình'}, status=400)

        user.is_active = False
        user.save()
        logger.info(f"[ADMIN] Vô hiệu hóa user: {user.username}")
        return Response({'message': f'Đã vô hiệu hóa {user.username}'})


# ════════════════════════════════════════
#  ADDRESS
# ════════════════════════════════════════

class AddressListView(APIView):
    """
    GET  /users/me/addresses/       → Danh sách địa chỉ
    POST /users/me/addresses/       → Thêm địa chỉ
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = request.user.addresses.all()
        return Response(UserAddressSerializer(addresses, many=True).data)

    def post(self, request):
        serializer = UserAddressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        # Nếu chưa có địa chỉ nào → mặc định is_default
        if not request.user.addresses.exists():
            serializer.validated_data['is_default'] = True
        address = serializer.save(user=request.user)
        return Response(UserAddressSerializer(address).data, status=201)


class AddressDetailView(APIView):
    """
    PUT    /users/me/addresses/:id/  → Cập nhật
    DELETE /users/me/addresses/:id/  → Xóa
    PATCH  /users/me/addresses/:id/set-default/ → Đặt làm mặc định
    """
    permission_classes = [IsAuthenticated]

    def get_address(self, request, pk):
        try:
            return UserAddress.objects.get(pk=pk, user=request.user)
        except UserAddress.DoesNotExist:
            return None

    def put(self, request, pk):
        addr = self.get_address(request, pk)
        if not addr:
            return Response({'error': 'Không tìm thấy địa chỉ'}, status=404)
        serializer = UserAddressSerializer(addr, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        addr = self.get_address(request, pk)
        if not addr:
            return Response({'error': 'Không tìm thấy địa chỉ'}, status=404)
        addr.delete()
        return Response({'message': 'Đã xóa địa chỉ'}, status=204)


class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            addr = UserAddress.objects.get(pk=pk, user=request.user)
            addr.is_default = True
            addr.save()  # Model.save() tự xử lý bỏ default cũ
            return Response({'message': 'Đã đặt làm địa chỉ mặc định'})
        except UserAddress.DoesNotExist:
            return Response({'error': 'Không tìm thấy địa chỉ'}, status=404)


# ════════════════════════════════════════
#  HEALTH CHECK
# ════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """GET /users/health/"""
    from django.db import connection
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return Response({
        'service': 'user-service',
        'status':  'ok' if db_ok else 'degraded',
        'database': 'connected' if db_ok else 'error',
        'version': '1.0.0',
    })


# ════════════════════════════════════════
#  STATS (Dashboard)
# ════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAdmin])
def user_stats(request):
    """GET /users/stats/ — Dùng cho dashboard admin"""
    return Response({
        'total':     User.objects.count(),
        'admins':    User.objects.filter(role='admin').count(),
        'staff':     User.objects.filter(role='staff').count(),
        'customers': User.objects.filter(role='customer').count(),
        'active':    User.objects.filter(is_active=True).count(),
        'inactive':  User.objects.filter(is_active=False).count(),
    })