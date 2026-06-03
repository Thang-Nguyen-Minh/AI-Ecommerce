# shipping-service

Microservice quản lý **vận chuyển đơn hàng** — service cuối trong luồng. order-service gọi tới sau khi thanh toán thành công để tạo phiếu giao; staff đẩy trạng thái tới khi giao xong.

---

## Stack

| Thành phần | Chi tiết |
|------------|---------|
| Framework  | Django + DRF |
| Database   | MySQL 8.0 (`ecom-shipping-db`) |
| Port       | `8006` (host) → `8000` (container) |
| Auth       | Tạo phiếu: nội bộ (không token). Cập nhật: staff/admin (JWT user-service) |

---

## Data model — Shipment (`shipment`)

| Field      | Kiểu     | Ràng buộc                               |
|------------|----------|-----------------------------------------|
| id         | int      | PK, auto                                |
| order_id   | int      | **unique** — mỗi đơn một phiếu          |
| address    | text     | bắt buộc                                |
| status     | string   | `Processing` / `Shipping` / `Delivered` |
| created_at, updated_at | datetime | auto                        |

---

## Business Rules

| ID   | Quy tắc |
|------|---------|
| BR-1 | `address` bắt buộc — thiếu → 400 |
| BR-2 | Trạng thái chỉ tiến: `Processing → Shipping → Delivered`. Nhảy cóc/lùi → 400 |
| BR-3 | Chỉ đơn đã thanh toán mới có shipment (order-service đảm bảo — chỉ gọi khi payment Success) |
| BR-4 | `order_id` unique — gọi create lần 2 → trả phiếu cũ, không tạo mới |
| BR-5 | Create nội bộ (không expose gateway); cập nhật chỉ staff/admin |
| BR-6 | Khách chỉ xem được trạng thái đơn của mình |

---

## API

Base URL: `http://shipping-service:8000` (Docker) / `http://localhost:8006` (chạy tay)

| Method | Path                | Quyền       | Body / Query           | Response |
|--------|---------------------|-------------|------------------------|----------|
| POST   | `/shipping/create`  | nội bộ      | `{order_id, address}`  | 201 phiếu (200 nếu đã tồn tại) |
| GET    | `/shipping/status`  | xem         | `?order_id=<id>`       | 200 `{order_id, status}` / 404 |
| PATCH  | `/shipping/<id>`    | staff/admin | `{status}`             | 200 phiếu / 400 / 403 |
| GET    | `/shipping/health/` | —           | —                      | 200 |

---

## Test — TC-01→TC-09 ✅

```bash
# TC-01: tạo phiếu (nội bộ)
curl -X POST http://localhost:8006/shipping/create -H "Content-Type: application/json" \
  -d '{"order_id":1,"address":"123 Le Loi"}'

# TC-05: staff đẩy trạng thái (cần staff token)
curl -X PATCH http://localhost:8006/shipping/1 -H "Authorization: Bearer <STAFF>" \
  -H "Content-Type: application/json" -d '{"status":"Shipping"}'
```

### Definition of Done
- [x] TC-01→TC-07 pass; TC-08 (không lộ gateway → 404); TC-09 (tích hợp order)
- [x] Trạng thái chỉ tiến Processing→Shipping→Delivered
- [x] Tạo phiếu nội bộ; cập nhật chỉ staff/admin (RBAC)
- [x] Mỗi order_id một shipment

---

## Kiểm thử đầu-cuối toàn hệ thống (mục 8 của contract)

Chạy `test-e2e.sh` ở thư mục gốc dự án khi cả 6 service đều chạy. Kiểm chứng 2 kịch bản:
- **Happy path**: login → giỏ → đơn → payment Success → shipment Processing → staff đẩy Delivered → đơn SHIPPED.
- **Fail path**: `simulate:"fail"` → payment Failed → order PAYMENT_FAILED → **không** có shipment (404).

Đây là bằng chứng cho luật tài liệu 4.7.2: "payment success → mới gọi shipping".
