from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserAddress


# ── JWT Custom — thêm role vào payload ──────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id']   = user.id
        token['username']  = user.username
        token['role']      = user.role
        token['full_name'] = user.display_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Trả về thêm thông tin user trong response login
        data['user'] = UserDetailSerializer(self.user).data
        data['tokens'] = {
            'access':  data.pop('access'),
            'refresh': data.pop('refresh'),
        }
        return data


# ── Register API (Email-based) ───────────────────────
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email là bắt buộc',
            'blank': 'Email không được để trống',
            'invalid': 'Email không hợp lệ',
        },
    )
    password = serializers.CharField(
        min_length=8, write_only=True, required=True,
        error_messages={
            'required': 'Mật khẩu là bắt buộc',
            'blank': 'Mật khẩu không được để trống',
            'min_length': 'Mật khẩu phải có ít nhất 8 ký tự',
        },
    )
    full_name = serializers.CharField(max_length=200, required=False, default='')
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    occupation = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    address = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email này đã được đăng ký')
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError('Email không hợp lệ')
        return value.lower()

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data.get('full_name', '')
        phone = validated_data.get('phone', '')
        occupation = validated_data.get('occupation', '')
        address = validated_data.get('address', '').strip()

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            occupation=occupation,
            role='customer',  # BR-1: luôn customer, không nhận từ client
        )
        # Nếu khách nhập địa chỉ lúc đăng ký → tạo địa chỉ mặc định
        if address:
            UserAddress.objects.create(
                user=user,
                full_name=full_name or email,
                phone=phone,
                street=address,
                district='',
                city='',
                is_default=True,
            )
        return user


# ── Login API (Email-based) ──────────────────────────
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password', '')

        if not email or not password:
            raise serializers.ValidationError('Email và password là bắt buộc')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Sai thông tin đăng nhập')

        if not user.check_password(password):
            raise serializers.ValidationError('Sai thông tin đăng nhập')

        if not user.is_active:
            raise serializers.ValidationError('Tài khoản bị khóa')

        data['user'] = user
        return data


# ── Address ──────────────────────────────────────────
class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserAddress
        fields = ['id', 'full_name', 'phone', 'street',
                  'ward', 'district', 'city', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']


# ── User Detail ──────────────────────────────────────
class UserDetailSerializer(serializers.ModelSerializer):
    addresses = UserAddressSerializer(many=True, read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 'occupation',
            'avatar', 'role', 'role_display', 'is_active',
            'created_at', 'updated_at', 'addresses',
        ]
        read_only_fields = ['id', 'username', 'role', 'is_active', 'created_at', 'updated_at']


# ── User List (Admin) ─────────────────────────────────
class UserListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    address_count = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'full_name', 'phone',
                  'role', 'role_display', 'is_active', 'created_at', 'address_count']

    def get_address_count(self, obj):
        return obj.addresses.count()


# ── User Serializer (for GET /users/) ────────────────
class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'phone', 'role', 'role_display', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


# ── Admin tạo staff/admin (BR-2) ─────────────────────
class AdminCreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    role = serializers.ChoiceField(choices=['admin', 'staff'], required=True)
    full_name = serializers.CharField(max_length=200, required=False, default='')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email này đã được đăng ký')
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role'],
            full_name=validated_data.get('full_name', ''),
        )


# ── Update Profile ────────────────────────────────────
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['full_name', 'phone', 'occupation', 'avatar']


# ── Change Password ───────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Mật khẩu mới không khớp'})

        validate_password(data['new_password'])
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mật khẩu cũ không đúng')
        return value
