# order-service

Microservice quản lý **đơn hàng và vòng đời đơn**. Là service **điều phối (orchestrator)**: tạo đơn từ giỏ → gọi payment → (thành công) gọi shipping.

---

## Stack

| Thành phần | Chi tiết |
|------------|---------|
| Framework  | Django + DRF |
| Database   | PostgreSQL (`ecom-order-db`) |
| Port       | `8004` (host) → `8000` (container) |
| Auth       | JWT của user-service (RemoteUserJWTAuthentication, không tra DB) |

Gọi sang: cart-service (đọc giỏ), product-service (giá + tồn kho), payment-service (thanh toán), shipping-service (giao hàng).

---

## Data model

**Order** (`orders`): `id, user_id, total_price, status, shipping_address, created_at`
**OrderItem** (`order_item`): `id, order(FK), product_id, quantity, unit_price`

> `unit_price` chốt giá tại thời điểm đặt — đơn cũ không bị sai khi product-service đổi giá.

### Trạng thái đơn
`PENDING` → `PAID` → `SHIPPED` → `DELIVERED`. Nhánh lỗi: `PAYMENT_FAILED`, `CANCELLED`.

---

## Business Rules

| ID   | Quy tắc |
|------|---------|
| BR-1 | `user_id` lấy từ JWT, bỏ qua trong body |
| BR-2 | Giỏ rỗng → không tạo đơn (400) |
| BR-3 | `total_price` server tính = Σ(giá thật × qty), bỏ qua giá client gửi |
| BR-4 | Kiểm lại tồn kho lúc đặt (đọc product-service) |
| BR-5 | Gọi payment trước; **chỉ khi Success** mới gọi shipping |
| BR-6 | Chỉ xem/tạo đơn của chính mình (403 khi xem đơn người khác) |
| BR-7 | payment/shipping lỗi → đơn không nửa vời, không có shipment mồ côi |

---

## API

Base URL: `http://localhost:8004`

| Method | Path           | Body                          | Response |
|--------|----------------|-------------------------------|----------|
| POST   | `/orders/`     | `{shipping_address, simulate?}` | 201 đơn + items / 400 / 503 |
| GET    | `/orders/`     | —                             | 200 danh sách đơn của user |
| GET    | `/orders/<id>` | —                             | 200 chi tiết / 403 / 404 |

### Luồng `POST /orders/`
```
đọc giỏ (cart) → kiểm tồn (product) → tính tổng → tạo đơn PENDING
  → gọi payment /payment/pay
      ├─ unreachable (sập/timeout) → 503, đơn PAYMENT_FAILED, KHÔNG shipping, giỏ giữ nguyên
      ├─ trả Failed                → 201, đơn PAYMENT_FAILED, KHÔNG shipping
      └─ trả Success               → đơn PAID → gọi shipping
                                        ├─ shipping OK   → SHIPPED
                                        └─ shipping chưa có → giữ PAID
                                     → dọn giỏ (chống đặt trùng)
```

> `simulate` (vd `"fail"`) chỉ để test — forward xuống payment sandbox. Production bỏ qua.

---

## Biến môi trường

| Biến | Giá trị (Docker) |
|------|------------------|
| `CART_SERVICE_URL`     | `http://cart-service:8000` |
| `PRODUCT_SERVICE_URL`  | `http://product-service:8000` |
| `PAYMENT_SERVICE_URL`  | `http://payment-service:8000` |
| `SHIPPING_SERVICE_URL` | `http://shipping-service:8000` |

Mọi lời gọi liên service đều có timeout 5s.

---

## Test

### Giai đoạn A (cần user + product + cart) — TC-01→TC-07 ✅
```bash
# Thêm hàng vào giỏ trước (cart-service), rồi:
curl -X POST http://localhost:8004/orders/ -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" -d '{"shipping_address":"123 Le Loi"}'
```

### Giai đoạn B (cần payment-service) — TC-08→TC-11 ✅
- TC-08: payment Success → đơn `PAID` (→ `SHIPPED` khi shipping-service sẵn sàng)
- TC-09: `{"simulate":"fail"}` → đơn `PAYMENT_FAILED`, không shipping
- TC-10: tắt payment → `503`, đơn `PAYMENT_FAILED`, không shipment
- TC-11: đặt 2 lần → lần 2 báo giỏ trống (giỏ đã dọn)

> **Trạng thái hiện tại**: payment đã wired đầy đủ. Đơn dừng ở `PAID` cho tới khi
> shipping-service được dựng — lúc đó luồng tự động đạt `SHIPPED` (TC-08 trọn vẹn).
