# ecom-final

Hệ thống thương mại điện tử xây dựng theo kiến trúc **Microservices**, phục vụ môn học **Kiến trúc và Thiết kế Phần mềm (SoAD)**.

---

## Kiến trúc tổng quan

```
                          ┌─────────────────────────────────────┐
Browser / Client          │            Nginx Gateway             │  :80
                          │   (định tuyến theo path prefix)      │
                          └────┬────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────────────────┐
          │                    │                                 │
     /auth/ /users/      /products/                        / (frontend)
          │                    │                                 │
    ┌─────▼──────┐      ┌──────▼─────┐                  ┌───────▼──────┐
    │user-service│      │product-svc │                  │  frontend    │
    │  :8001     │      │   :8002    │                  │ (nginx static)│
    └─────┬──────┘      └──────┬─────┘                  └──────────────┘
          │                    │
    ┌─────▼──────┐      ┌──────▼─────┐
    │  MySQL     │      │ PostgreSQL  │
    │ user_db    │      │ product_db  │
    └────────────┘      └────────────┘

  /cart/       → cart-service    :8003  → MySQL (cart_db)
  /orders/     → order-service   :8004  → PostgreSQL (order_db)
  /payments/   → payment-service :8005  → MySQL (payment_db)
  /shipping/   → shipping-service:8006  → MySQL (shipping_db)
  /ai/         → ai-service      :8007  → Neo4j + Redis

  Shared: Redis (cache/queue), Neo4j (Knowledge Graph)
```

---

## Services

| Service          | Stack          | DB         | Port  | Status   |
|------------------|----------------|------------|-------|----------|
| user-service     | Django + DRF   | MySQL      | 8001  | ✅ Done  |
| product-service  | Django + DRF   | PostgreSQL | 8002  | ✅ Done  |
| cart-service     | Django + DRF   | MySQL      | 8003  | ✅ Done  |
| order-service    | Django + DRF   | PostgreSQL | 8004  | ✅ Done  |
| payment-service  | Django + DRF   | MySQL      | 8005  | ✅ Done  |
| shipping-service | Django + DRF   | MySQL      | 8006  | ✅ Done  |
| ai-service       | FastAPI        | Neo4j      | 8007  | 🔧 WIP   |
| frontend         | HTML/JS/Bootstrap | —       | 80    | ✅ Done  |
| gateway          | Nginx          | —          | 80    | ✅ Done  |

---

## Yêu cầu hệ thống

- **Docker Desktop** (Windows/macOS) hoặc **Docker Engine** (Linux)
- Docker Compose v2 (`docker compose` — không dùng `docker-compose`)
- RAM: tối thiểu 4 GB cho Docker
- Disk: ~3–4 GB (images + volumes)

---

## Khởi động nhanh

### Bước 1 — Cấu hình môi trường

```bash
cp .env.example .env
# Sửa .env nếu cần đổi mật khẩu
```

### Bước 2 — Build base image (chỉ cần chạy lần đầu)

```bash
make build-base
# Windows không có make:
build-base.bat
```

### Bước 3 — Khởi động toàn bộ hệ thống

```bash
make up
# hoặc:
docker compose up -d
# Windows:
up.bat
```

### Bước 4 — Kiểm tra trạng thái

```bash
docker compose ps
# Tất cả service phải healthy trước khi dùng
```

### Bước 5 — Mở trình duyệt

| URL | Mô tả |
|-----|-------|
| http://localhost/ | Frontend (trang chủ) |
| http://localhost/login.html | Đăng nhập |
| http://localhost/register.html | Đăng ký |
| http://localhost/products.html | Danh sách sản phẩm |
| http://localhost/profile.html | Hồ sơ cá nhân |
| http://localhost/admin/dashboard.html | Bảng quản trị (admin) |
| http://localhost:7474/ | Neo4j Browser |

---

## Dừng / Dọn dẹp

```bash
# Dừng, giữ data
make down        # hoặc: down.bat

# Dừng + xóa toàn bộ volume (mất data)
docker compose down -v

# Xóa images cũ + build lại
make rebuild     # hoặc: rebuild.bat
```

---

## Tài khoản thử nghiệm

Tạo admin đầu tiên bằng lệnh:

```bash
docker exec -it ecom-user-service python manage.py shell -c "
from users.models import User
User.objects.create_superuser(
    username='admin@ecom.local',
    email='admin@ecom.local',
    password='Admin123!',
    role='admin'
)"
```

Sau đó đăng nhập tại `/login.html` với email `admin@ecom.local`.

Tạo dữ liệu demo cho Product Service:

```bash
curl -X POST http://localhost:8002/products/seed-demo/
```

---

## API nhanh

### User Service (`:8001`)

```bash
# Đăng ký
curl -X POST http://localhost:8001/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"khach@test.com","password":"MatKhau123!"}'

# Đăng nhập
curl -X POST http://localhost:8001/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"khach@test.com","password":"MatKhau123!"}'
```

### Product Service (`:8002`)

```bash
# Danh sách sản phẩm
curl http://localhost:8002/products/

# Tạo dữ liệu demo
curl -X POST http://localhost:8002/products/seed-demo/
```

---

## Kiểm thử đầu-cuối

Khi cả 6 service đang chạy, chạy script kiểm thử toàn hệ thống (chứng minh luồng tài liệu 4.7.2):

```bash
bash test-e2e.sh
```

Script kiểm chứng 2 kịch bản:
- **Happy path**: login → giỏ → đơn → payment Success → shipment → staff đẩy Delivered (đơn `SHIPPED`)
- **Fail path**: `simulate:"fail"` → payment Failed → đơn `PAYMENT_FAILED` → **không** có shipment (404)

Mỗi service còn có test case riêng trong `*/contract_*.md` (mục 5) — chạy được bằng `curl` không cần đọc code.

---

## Cấu trúc thư mục

```
ecom-final/
├── .env.example            ← mẫu cấu hình (commit)
├── .env                    ← cấu hình thật (KHÔNG commit)
├── .gitignore
├── docker-compose.yml      ← cấu hình toàn bộ hệ thống
├── entrypoint.sh           ← entrypoint chung cho Django services
├── Makefile                ← lệnh tắt (make up, make down, ...)
│
├── gateway/
│   └── nginx.conf          ← routing rules
│
├── frontend/
│   └── src/                ← HTML, CSS, JS tĩnh
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       ├── profile.html
│       ├── products.html
│       ├── admin/
│       │   ├── dashboard.html
│       │   └── users.html
│       └── js/
│           ├── api.js      ← API client dùng chung
│           └── ...
│
├── user-service/           ← xác thực, user, địa chỉ
│   ├── README.md           ← tài liệu riêng + test cases
│   ├── contract_user-service.md
│   └── users/
│
├── product-service/        ← danh mục, sản phẩm
├── cart-service/
├── order-service/
├── payment-service/
├── shipping-service/
├── ai-service/
│
├── base-images/            ← Dockerfile base cho Django services
└── infrastructure/
    └── db/                 ← SQL init scripts
```

---

## Nguyên tắc thiết kế

| Nguyên tắc | Áp dụng |
|-----------|---------|
| Database-per-service | Mỗi service có DB riêng, không truy cập DB service khác |
| Bounded Context (DDD) | Mỗi service chỉ chịu trách nhiệm domain của mình |
| JWT stateless | User-service cấp token có chứa `role` — service khác tự xác thực mà không cần gọi lại user-service |
| API-first | Mỗi service có contract + test case trước khi code |
| Single entry point | Tất cả request đi qua Nginx gateway |

---

## Xem log

```bash
docker compose logs -f user-service
docker compose logs -f product-service
docker compose logs -f nginx
# Windows scripts:
logs-user.bat
logs-product.bat
```

---

## Khắc phục sự cố thường gặp

| Triệu chứng | Nguyên nhân phổ biến | Cách xử lý |
|-------------|---------------------|------------|
| `502 Bad Gateway` | Service đích chưa healthy | Chờ hoặc `docker compose restart <service>` |
| Service cứ `unhealthy` | DB/Redis chưa sẵn sàng | Kiểm tra DB container trước |
| `Port already in use` | Port 80/8001… đang bị dùng | Dừng tiến trình khác hoặc đổi port trong compose |
| Container không start | Thiếu `.env` | Chạy `cp .env.example .env` |
| `ModuleNotFoundError` | Chưa build base image | Chạy `make build-base` |

---

## Tài liệu liên quan

- [`user-service/README.md`](user-service/README.md) — API + test cases user-service
- [`user-service/contract_user-service.md`](user-service/contract_user-service.md) — Contract + nghiệm thu
- [`docker-compose.yml`](docker-compose.yml) — Cấu hình hạ tầng đầy đủ
- [`Makefile`](Makefile) — Lệnh tắt
- [`gateway/nginx.conf`](gateway/nginx.conf) — Routing rules

---

## License

Dự án học tập — môn Kiến trúc và Thiết kế Phần mềm, GVHD: Trần Đình Quế.
