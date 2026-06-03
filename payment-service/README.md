# payment-service

Microservice xử lý **giao dịch thanh toán cho đơn hàng**. Là service **nội bộ** — chỉ order-service gọi tới (server-to-server), không expose ra khách qua gateway.

---

## Stack

| Thành phần | Chi tiết |
|------------|---------|
| Framework  | Django + DRF |
| Database   | MySQL 8.0 (`ecom-payment-db`) |
| Port       | `8005` (host) → `8000` (container) |
| Auth       | Không xác thực token người dùng (nội bộ — BR-4) |

---

## Data model — Payment (`payment`)

| Field      | Kiểu        | Ràng buộc                          |
|------------|-------------|------------------------------------|
| id         | int         | PK, auto                           |
| order_id   | int         | **unique** — mỗi đơn một giao dịch |
| amount     | decimal     | > 0                                |
| status     | string      | `Pending` / `Success` / `Failed`   |
| created_at | datetime    | auto                               |

---

## Business Rules

| ID   | Quy tắc |
|------|---------|
| BR-1 | Mỗi giao dịch gắn với một `order_id`; `amount` do order-service gửi sang |
| BR-2 | `amount > 0` — số tiền ≤ 0 bị từ chối (400) |
| BR-3 | Chống charge trùng: `order_id` đã có giao dịch → trả lại bản ghi cũ, không tạo mới |
| BR-4 | `/payment/pay` chỉ gọi nội bộ, không định tuyến qua gateway |
| BR-5 | Trạng thái cuối (Success/Failed) không bị ghi đè |
| BR-6 | Sandbox (`PAYMENT_SANDBOX=true`): `simulate:"fail"` → Failed; mặc định Success |

---

## API (nội bộ)

Base URL: `http://payment-service:8000` (Docker) / `http://localhost:8005` (chạy tay)

| Method | Path              | Body / Query                    | Response                                |
|--------|-------------------|---------------------------------|-----------------------------------------|
| POST   | `/payment/pay`    | `{order_id, amount, simulate?}` | 201 `{id, order_id, amount, status}` (200 nếu đã tồn tại) |
| GET    | `/payment/status` | `?order_id=<id>`                | 200 `{order_id, status}` / 404          |
| GET    | `/payment/health/`| —                               | 200 health                              |

Mã lỗi: `400` amount sai, `404` không có giao dịch (khi query).

---

## Biến môi trường

| Biến             | Mặc định | Ghi chú |
|------------------|----------|---------|
| `PAYMENT_SANDBOX`| `true`   | `true` ở dev để ép Failed test nhánh lỗi. **Đặt `false` ở production** — cờ `simulate` bị bỏ qua |
| `DB_*`           | MySQL    | DB riêng `payment_db` |

---

## Test (chạy được ngay — không cần token)

```bash
# TC-01: thanh toán hợp lệ → Success
curl -X POST http://localhost:8005/payment/pay -H "Content-Type: application/json" \
  -d '{"order_id":1,"amount":240000}'

# TC-05: ép thất bại (sandbox) → Failed
curl -X POST http://localhost:8005/payment/pay -H "Content-Type: application/json" \
  -d '{"order_id":3,"amount":100000,"simulate":"fail"}'

# TC-03: tra trạng thái
curl "http://localhost:8005/payment/status?order_id=1"
```

### Definition of Done
- [x] TC-01 → TC-06 pass
- [x] TC-07: `/payment/pay` không truy cập được qua gateway (404)
- [x] Trạng thái chỉ Pending/Success/Failed; terminal không đổi
- [x] Không charge trùng cho cùng order_id
- [x] Sandbox ép Failed ở dev (cho order TC-09)

> Lưu ý gateway: hiện `gateway/nginx.conf` có block `/api/payments/` trỏ tới payment-service
> nhưng không khớp endpoint thật (`/payment/pay`) nên không lộ — khi dọn gateway nên bỏ block này.
