from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra):
        if not email:
            raise ValueError('Email là bắt buộc')
        email = self.normalize_email(email)
        user  = self.model(username=username, email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra):
        extra.setdefault('role', 'admin')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin',    '👑 Admin'),
        ('staff',    '🛠 Staff'),
        ('customer', '👤 Customer'),
    ]

    username   = models.CharField(max_length=100, unique=True)
    email      = models.EmailField(max_length=255, unique=True)
    full_name  = models.CharField(max_length=200, blank=True, default='')
    phone      = models.CharField(max_length=20,  blank=True, default='')
    occupation = models.CharField(max_length=120, blank=True, default='', help_text='Nghề nghiệp — phục vụ knowledge graph (Neo4j)')
    avatar     = models.URLField(blank=True, default='')
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users_user'
        ordering = ['-created_at']
        verbose_name      = 'Người dùng'
        verbose_name_plural = 'Người dùng'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff_member(self):
        return self.role in ('admin', 'staff')

    @property
    def display_name(self):
        return self.full_name or self.username


class UserAddress(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name  = models.CharField(max_length=200)
    phone      = models.CharField(max_length=20)
    street     = models.CharField(max_length=255)
    ward       = models.CharField(max_length=100, blank=True, default='')
    district   = models.CharField(max_length=100)
    city       = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_address'
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Địa chỉ'
        verbose_name_plural = 'Địa chỉ'

    def __str__(self):
        return f"{self.street}, {self.district}, {self.city}"

    def save(self, *args, **kwargs):
        # Nếu set is_default=True → bỏ default ở các địa chỉ khác
        if self.is_default:
            UserAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)