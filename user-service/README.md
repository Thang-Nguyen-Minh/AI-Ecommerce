# user-service

Microservice quản lý **danh tính và phân quyền** trong hệ thống ecom-final.

---

## Phạm vi (Bounded Context)

- Đăng ký, đăng nhập, cấp JWT
- Lưu thông tin người dùng và vai trò (role: admin / staff / customer)
- Quản lý địa chỉ giao hàng
- Cung cấp thông tin xác thực cho các service khác qua JWT claim

**Không** thuộc phạm vi: giỏ hàng, đơn hàng, sản phẩm.

---

## Stack

| Thành phần | Chi tiết |
|------------|---------|
| Framework  | Django 4.x + Django REST Framework |
| Auth       | `djangorestframework-simplejwt` (JWT) |
| Database   | MySQL 8.0 (container: `ecom-user-db`) |
| Port       | `8001` (host) → `8000` (container) |

---

## Data Model

### User
| Field       | Kiểu       | Ghi chú                                   |
|-------------|------------|-------------------------------------------|
| id          | int        | PK, auto                                  |
| username    | string     | unique — được set bằng email khi đăng ký  |
| email       | string     | unique, dùng để đăng nhập                 |
| password    | string     | lưu dạng hash (pbkdf2_sha256)             |
| full_name   | string     | tên hiển thị                              |
| phone       | string     | tuỳ chọn                                  |
| role        | string     | `admin` / `staff` / `customer` (mặc định) |
| is_active   | bool       | mặc định `true`                           |
| created_at  | datetime   | auto                                      |

### UserAddress
| Field      | Kiểu    | Ghi chú                                       |
|------------|---------|-----------------------------------------------|
| id         | int     | PK, auto                                      |
| user       | FK      | → User                                        |
| full_name  | string  | tên người nhận                                |
| phone      | string  | SĐT nhận hàng                                 |
| street     | string  | số nhà, tên đường                             |
| ward       | string  | phường/xã (tuỳ chọn)                          |
| district   | string  | quận/huyện                                    |
| city       | string  | tỉnh/thành phố                                |
| is_default | bool    | **Business rule**: khi set true → tự động bỏ default các địa chỉ khác |

---

## Business Rules

| ID   | Quy tắc |
|------|---------|
| BR-1 | Người dùng tự đăng ký qua `/auth/register/` **luôn** được gán `role = customer` — không nhận role từ client |
| BR-2 | Chỉ **admin** mới được tạo tài khoản `staff` hoặc `admin` (qua `POST /users/` với token admin) |
| BR-3 | Password lưu dạng hash, không endpoint nào trả password về client |
| BR-4 | Email là unique — đăng ký trùng email bị từ chối |
| BR-5 | JWT access token chứa claim `role`, `username`, `full_name` để service khác đọc quyền |
| BR-6 | RBAC — xem bảng phân quyền bên dưới |

### Ma trận phân quyền (BR-6)

| Hành động                  | admin | staff | customer |
|----------------------------|:-----:|:-----:|:--------:|
| Xem danh sách toàn bộ user |  ✅   |  ❌   |    ❌    |
| Tạo tài khoản staff/admin  |  ✅   |  ❌   |    ❌    |
| Xem/sửa hồ sơ của mình    |  ✅   |  ✅   |    ✅    |
| Xem/sửa địa chỉ của mình  |  ✅   |  ✅   |    ✅    |
| Đổi mật khẩu              |  ✅   |  ✅   |    ✅    |
| Xem/sửa bất kỳ user       |  ✅   |  ❌   |    ❌    |

---

## API Endpoints

Base URL khi chạy qua Docker: `http://localhost:8001`  
Qua Nginx gateway: `http://localhost` (path giữ nguyên)

### Auth

| Method | Path                  | Auth     | Body                             | Response              |
|--------|-----------------------|----------|----------------------------------|-----------------------|
| POST   | `/auth/register/`     | Public   | `{email, password, full_name?}`  | 201 `{id, email, role}` |
| POST   | `/auth/login/`        | Public   | `{email, password}`              | 200 `{access, refresh, user}` |
| POST   | `/auth/logout/`       | Token    | `{refresh}`                      | 200                   |
| POST   | `/auth/refresh/`      | Public   | `{refresh}`                      | 200 `{access}`        |

### Profile (người dùng hiện tại)

| Method | Path                                    | Auth  | Body                              | Response              |
|--------|-----------------------------------------|-------|-----------------------------------|-----------------------|
| GET    | `/users/me/`                            | Token | —                                 | 200 user + addresses  |
| PUT    | `/users/me/`                            | Token | `{full_name?, phone?, avatar?}`   | 200                   |
| POST   | `/users/me/change-password/`            | Token | `{old_password, new_password, new_password2}` | 200    |
| GET    | `/users/me/addresses/`                  | Token | —                                 | 200 list              |
| POST   | `/users/me/addresses/`                  | Token | `{full_name, phone, street, ward?, district, city, is_default?}` | 201 |
| PUT    | `/users/me/addresses/<id>/`             | Token | fields địa chỉ                    | 200                   |
| DELETE | `/users/me/addresses/<id>/`             | Token | —                                 | 204                   |
| POST   | `/users/me/addresses/<id>/set-default/` | Token | —                                 | 200                   |

### Admin

| Method | Path              | Auth  | Body                                   | Response              |
|--------|-------------------|-------|----------------------------------------|-----------------------|
| GET    | `/users/`         | Admin | —                                      | 200 list all users    |
| POST   | `/users/`         | Admin | `{email, password, role, full_name?}`  | 201 `{id, email, role}` |
| GET    | `/users/<id>/`    | Admin | —                                      | 200 user detail       |
| PUT    | `/users/<id>/`    | Admin | `{full_name?, role?, is_active?}`      | 200                   |
| DELETE | `/users/<id>/`    | Admin | —                                      | 200 (soft delete — set is_active=false) |
| GET    | `/users/stats/`   | Admin | —                                      | 200 thống kê số lượng |
| GET    | `/users/health/`  | Public| —                                      | 200 health status     |

### Mã lỗi

| Code | Ý nghĩa |
|------|---------|
| 400  | Dữ liệu sai / trùng |
| 401  | Không có hoặc sai token |
| 403  | Token đúng nhưng không đủ quyền |
| 404  | Không tìm thấy |

---

## Test Cases (chạy được ngay)

Xem chi tiết trong [contract_user-service.md](contract_user-service.md).

Tóm tắt nhanh:

```bash
# TC-01: Đăng ký → 201, role=customer
curl -s -X POST http://localhost:8001/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"MatKhau123!"}'

# TC-02: Không cho leo quyền → vẫn là customer
curl -s -X POST http://localhost:8001/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"hacker@test.com","password":"x123456!","role":"admin"}'

# TC-04: Login → JWT có role claim
curl -s -X POST http://localhost:8001/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"MatKhau123!"}'

# TC-07: Customer không xem được danh sách user → 403
curl -s http://localhost:8001/users/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>"
```

### Definition of Done

- [ ] TC-01 → TC-09 trong contract đều pass
- [ ] JWT access token chứa claim `role`
- [ ] Không endpoint công khai nào tạo được admin
- [ ] Password không bao giờ xuất hiện trong response

---

## Cách chạy riêng lẻ (không dùng docker-compose)

```bash
cd user-service

# Tạo và activate venv
python -m venv .venv
.venv\Scripts\activate      # Windows
# hoặc: source .venv/bin/activate  # Linux/Mac

# Cài dependencies (cần có base requirements)
pip install django djangorestframework djangorestframework-simplejwt \
            django-cors-headers mysqlclient Pillow

# Cấu hình DB trong settings (hoặc dùng SQLite để test nhanh)
# Chạy migrations
python manage.py migrate

# Tạo superuser
python manage.py createsuperuser

# Khởi động
python manage.py runserver 8001
```

---

## Cấu trúc thư mục

```
user-service/
├── users/
│   ├── models.py        # User, UserAddress
│   ├── serializers.py   # RegisterSerializer, LoginSerializer, ...
│   ├── views.py         # LoginView, RegisterView, MeView, ...
│   ├── urls.py          # URL routing
│   └── permissions.py   # IsAdmin, IsAdminOrStaff, IsOwnerOrAdmin
├── ecom/
│   └── settings.py      # Django settings
├── manage.py
├── requirements.txt
├── Dockerfile
├── contract_user-service.md   # Đề bài + test cases nghiệm thu
└── README.md                  # File này
```
