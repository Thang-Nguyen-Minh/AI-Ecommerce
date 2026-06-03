from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserAddress


class UserAddressInline(admin.TabularInline):
    model  = UserAddress
    extra  = 0
    fields = ['full_name', 'phone', 'street', 'district', 'city', 'is_default']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['username', 'email', 'full_name']
    ordering      = ['-created_at']
    inlines       = [UserAddressInline]

    fieldsets = (
        (None,          {'fields': ('username', 'password')}),
        ('Thông tin',   {'fields': ('email', 'full_name', 'phone', 'avatar')}),
        ('Phân quyền',  {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('username', 'email', 'full_name', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display  = ['user', 'full_name', 'district', 'city', 'is_default']
    list_filter   = ['city', 'is_default']
    search_fields = ['user__username', 'full_name', 'phone']