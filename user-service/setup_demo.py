#!/usr/bin/env python
"""
Tự động tạo tài khoản demo khi khởi động lần đầu
Được gọi từ entrypoint.sh
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
django.setup()

from users.models import User, UserAddress

DEMO_USERS = [
    {
        'username':  'admin',
        'email':     'admin@ecom.vn',
        'password':  'Admin@123',
        'full_name': 'Quản Trị Viên',
        'phone':     '0901234567',
        'role':      'admin',
        'is_staff':  True,
        'is_superuser': True,
    },
    {
        'username':  'staff1',
        'email':     'staff1@ecom.vn',
        'password':  'Staff@123',
        'full_name': 'Nguyễn Văn Nam',
        'phone':     '0912345678',
        'role':      'staff',
    },
    {
        'username':  'customer1',
        'email':     'customer1@ecom.vn',
        'password':  'Customer@123',
        'full_name': 'Nguyễn Minh Thắng',
        'phone':     '0923456789',
        'role':      'customer',
    },
    {
        'username':  'customer2',
        'email':     'customer2@ecom.vn',
        'password':  'Customer@123',
        'full_name': 'Trần Thị Lan',
        'phone':     '0934567890',
        'role':      'customer',
    },
]

print("\n📦 Khởi tạo tài khoản demo...")
for u in DEMO_USERS:
    if User.objects.filter(username=u['username']).exists():
        print(f"   · Đã có: {u['username']}")
        continue
    user = User.objects.create_user(
        username  = u['username'],
        email     = u['email'],
        password  = u['password'],
        full_name = u['full_name'],
        phone     = u['phone'],
        role      = u['role'],
    )
    if u.get('is_staff'):
        user.is_staff      = True
        user.is_superuser  = True
        user.save()

    # Thêm địa chỉ mặc định
    UserAddress.objects.create(
        user       = user,
        full_name  = u['full_name'],
        phone      = u['phone'],
        street     = '123 Nguyễn Huệ',
        ward       = 'Phường Bến Nghé',
        district   = 'Quận 1',
        city       = 'TP. Hồ Chí Minh',
        is_default = True,
    )
    print(f"   ✓ Tạo {u['role']}: {u['username']} / {u['password']}")

print("✅ Demo accounts ready!\n")