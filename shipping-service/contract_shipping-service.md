# Contract: shipping-service

> Service cuối trong luồng. Chạy ở **cổng 8006** (đổi nếu cần). Bám sát tài liệu mục 2.8:
> model `Shipment(order_id, address, status)`, trạng thái Processing/Shipping/Delivered,
> API `/shipping/create` và `/shipping/status`. Bổ sung endpoint cập nhật trạng thái cho
> **staff** theo RBAC mục 2.4.3.
>
> shipping-service được **order-service gọi tới** sau khi thanh toán thành công (tài liệu
> 4.7.2). Nó đóng vòng luồng: payment success → tạo shipment → staff đẩy trạng thái tới
> Delivered.

---

## 1. Phạm vi (Bounded Context)

shipping-service quản lý **vận chuyển đơn hàng** (tài liệu 2.8):

- Tạo phiếu giao hàng (Shipment) cho một đơn đã thanh toán.
- Theo dõi và cập nhật trạng thái vận chuyển.
- Cho truy vấn trạng thái giao hàng theo đơn.

**Không** thuộc phạm vi: tạo đơn (order-service), xử lý tiền (payment-service). Không đụng
DB service khác.

---

## 2. Data model (bám sát tài liệu 2.8.1 / 2.10.4)

**Shipment** (bảng `shipment`)

| Field    | Kiểu        | Ràng buộc                              | Ghi chú                          |
|----------|-------------|----------------------------------------|----------------------------------|
| id       | int         | PK, auto                               |                                  |
| order_id | int         | bắt buộc, **unique**                   | tham chiếu sang order-service    |
| address  | text        | bắt buộc                               | địa chỉ giao, lấy từ đơn         |
| status   | string(50)  | trong {Processing, Shipping, Delivered}| mặc định `Processing`            |

> Ghi chú (cải tiến): đặt `order_id` **unique** để mỗi đơn chỉ có một phiếu giao (chống tạo
> trùng — xem BR-4); thêm `updated_at` để biết lần cập nhật trạng thái gần nhất. Tài liệu
> không bắt buộc nhưng nên có cho chuẩn.

---

## 3. Trạng thái & luật nghiệp vụ (Business Rules)

Trạng thái theo tài liệu 2.8.2, chỉ tiến theo thứ tự:
`Processing` → `Shipping` → `Delivered`.

- **BR-1**: Mỗi shipment gắn với một `order_id` và phải có `address`. Thiếu address → từ chối (400).
- **BR-2**: Trạng thái chỉ **tiến từng bước** theo thứ tự trên. Không cho nhảy cóc
  (Processing → Delivered) và không cho lùi (Shipping → Processing).
- **BR-3 (chỉ đơn đã thanh toán mới được giao)**: shipment chỉ được tạo cho đơn đã thanh toán
  thành công. Đảm bảo này do order-service thực thi (chỉ gọi `/shipping/create` khi payment
  Success — tài liệu 4.7.2). shipping-service tin lời gọi nội bộ này.
- **BR-4 (không tạo trùng)**: Một `order_id` chỉ có một shipment. Gọi `/shipping/create` lần
  hai cho cùng đơn → không tạo phiếu mới, trả lại phiếu cũ.
- **BR-5 (nội bộ + RBAC)**: `/shipping/create` chỉ gọi từ order-service (nội bộ), **không** lộ
  ra cho khách qua gateway. Cập nhật trạng thái (`PATCH`) chỉ dành cho **staff/admin** (RBAC
  2.4.3). Khách hàng chỉ được **xem** trạng thái đơn của mình.
- **BR-6**: Khách chỉ xem được shipment của đơn thuộc về mình (qua order-service / cách ly đơn).

---

## 4. API (hợp đồng với bên ngoài)

Base URL nội bộ: `http://shipping-service:8006` (Docker) / `http://localhost:8006` (chạy tay).

| Method | Đường dẫn          | Quyền cần       | Body / Query                | Trả ra (thành công)                          |
|--------|--------------------|-----------------|------------------------------|----------------------------------------------|
| POST   | /shipping/create   | nội bộ (order)  | `{order_id, address}`        | 201 + `{id, order_id, address, status}`      |
| GET    | /shipping/status   | xem (nội bộ/đơn)| `?order_id=<id>`             | 200 + `{order_id, status}`                   |
| PATCH  | /shipping/{id}     | staff/admin     | `{status}`                   | 200 + shipment sau cập nhật                  |

Mã lỗi: `400` thiếu address / chuyển trạng thái không hợp lệ, `401` thiếu token (với PATCH),
`403` không đủ quyền, `404` không thấy shipment.

> Hợp đồng: shipment tạo ra luôn bắt đầu ở `Processing`. order-service sau khi gọi tạo
> shipment thành công sẽ chuyển đơn sang `SHIPPED`. Trạng thái cuối `Delivered` do staff đẩy.

---

## 5. Tiêu chí nghiệm thu — Test API

Cần một staff token: dùng admin tạo tài khoản staff qua `POST /users/` ở user-service (theo
BR-2 của user-service), rồi staff login lấy token. Gọi nội bộ tới cổng 8006.

### TC-01 — Tạo phiếu giao cho đơn (BR-1, nội bộ)
```bash
curl -i -X POST http://localhost:8006/shipping/create \
  -H "Content-Type: application/json" \
  -d '{"order_id":1,"address":"123 Le Loi, Ha Noi"}'
```
Mong đợi: `201`, `status: "Processing"`, một shipment cho order_id=1.

### TC-02 — Thiếu địa chỉ bị chặn (BR-1)
```bash
curl -i -X POST http://localhost:8006/shipping/create \
  -H "Content-Type: application/json" \
  -d '{"order_id":2}'
```
Mong đợi: `400`, báo thiếu address. Không tạo phiếu.

### TC-03 — Truy vấn trạng thái theo đơn (tài liệu 2.8.3)
```bash
curl -i "http://localhost:8006/shipping/status?order_id=1"
```
Mong đợi: `200`, trả `{order_id:1, status:"Processing"}`.

### TC-04 — Không tạo phiếu trùng cho cùng đơn (BR-4)
Gọi lại TC-01 cho order_id=1.
Mong đợi: không tạo shipment thứ hai; trả lại phiếu cũ. DB chỉ có một shipment cho order_id=1.

### TC-05 — Staff đẩy trạng thái tiến đúng thứ tự (BR-2, RBAC) ⚠️ staff token
```bash
# Processing -> Shipping
curl -i -X PATCH http://localhost:8006/shipping/1 \
  -H "Authorization: Bearer <ACCESS_STAFF>" \
  -H "Content-Type: application/json" \
  -d '{"status":"Shipping"}'
# Shipping -> Delivered
curl -i -X PATCH http://localhost:8006/shipping/1 \
  -H "Authorization: Bearer <ACCESS_STAFF>" \
  -H "Content-Type: application/json" \
  -d '{"status":"Delivered"}'
```
Mong đợi: cả hai `200`; trạng thái cuối là `Delivered`.

### TC-06 — Chuyển trạng thái không hợp lệ bị chặn (BR-2)
Trên một shipment đang `Processing` (vd tạo order_id=3), thử nhảy thẳng tới Delivered, và thử lùi:
```bash
# Nhảy cóc Processing -> Delivered
curl -i -X PATCH http://localhost:8006/shipping/3 \
  -H "Authorization: Bearer <ACCESS_STAFF>" \
  -H "Content-Type: application/json" \
  -d '{"status":"Delivered"}'
```
Mong đợi: `400`. Tương tự, lùi `Delivered → Processing` cũng `400`.

### TC-07 — Khách hàng KHÔNG được cập nhật trạng thái (BR-5, RBAC) ⚠️ bảo mật
```bash
curl -i -X PATCH http://localhost:8006/shipping/1 \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"status":"Delivered"}'
```
Mong đợi: `403`. Chỉ staff/admin được đẩy trạng thái.

### TC-08 — Endpoint tạo phiếu không lộ ra ngoài (BR-5) ⚠️ bảo mật
Nếu đã có gateway, thử gọi `/shipping/create` qua URL công khai bằng token khách.
Mong đợi: `404`/`403`. (Chưa có gateway thì ghi là yêu cầu cấu hình ở chương 4.)

### TC-09 — Tích hợp với order: chỉ đơn đã trả tiền mới có shipment (BR-3) ⚠️ liên service
Đây cũng là TC-08/TC-09 của order-service nhìn từ phía shipping:
- Tạo đơn với thanh toán **thành công** → kiểm `GET /shipping/status?order_id=<đơn>` phải có
  shipment ở `Processing`.
- Tạo đơn với thanh toán **thất bại** (payment `simulate:"fail"`) → `GET .../status` cho đơn
  đó phải trả `404` (không có shipment). Chứng minh luật "payment success → shipping" của
  tài liệu 4.7.2 chạy đúng.

---

## 6. Kiểm tra giao diện (UI)

> Làm sau khi mục 5 xanh. Mỗi mục gắn một luật nghiệp vụ, có kết quả quan sát rõ ràng.

- [ ] **U-01 (BR-6)**: Khách mở chi tiết đơn đã thanh toán → thấy trạng thái giao hàng
  (Processing/Shipping/Delivered) đúng với dữ liệu.
- [ ] **U-02 (BR-2)**: Khi staff đẩy trạng thái, khách tải lại trang đơn → trạng thái cập nhật theo.
- [ ] **U-03 (BR-5)**: Màn hình của khách **không** có nút sửa trạng thái giao hàng; chỉ giao
  diện staff mới có.
- [ ] **U-04**: Đơn vừa thanh toán xong nhưng chưa có cập nhật → hiển thị "Đang xử lý", không
  để trống/vỡ layout.
- [ ] **U-05 (BR-3)**: Đơn thanh toán thất bại → phần giao hàng **không** hiển thị như đang
  giao (vì không có shipment).

---

## 7. Definition of Done (nghiệm thu xong khi)

- [ ] TC-01 → TC-07 pass; TC-08 pass (hoặc ghi nhận là cấu hình gateway); TC-09 pass.
- [ ] UI U-01 → U-05 pass.
- [ ] Trạng thái đúng tài liệu 2.8.2: Processing → Shipping → Delivered, chỉ tiến không lùi.
- [ ] Tạo phiếu là nội bộ; cập nhật trạng thái chỉ staff/admin (RBAC 2.4.3).
- [ ] Mỗi order_id chỉ một shipment (TC-04).
- [ ] Database riêng cho shipping-service.
- [ ] README ghi cách chạy (cổng 8006, không expose `/shipping/create` qua gateway).
- [ ] Đã `git commit` + `git tag shipping-service-ok`.

---

## 8. Kiểm thử đầu-cuối toàn hệ thống (đóng vòng — tài liệu 2.9 / 4.7.1)

Chạy khi cả 6 service đều `*-ok`. Đây là bài test chứng minh toàn hệ thống hoạt động đúng
luồng tài liệu — rất hợp để demo khi bảo vệ.

**Kịch bản thành công (happy path):**
1. Khách login (user-service :8000) → nhận token.
2. Xem sản phẩm (product-service :8002) → có hàng, stock > 0.
3. Thêm vào giỏ (cart-service :8003) → giỏ có item.
4. Tạo đơn (order-service :8004) → order-service đọc giỏ, tính tổng, gọi payment.
5. Thanh toán thành công (payment-service :8005) → trả Success.
6. order-service gọi shipping (shipping-service :8006) → shipment `Processing`, đơn `SHIPPED`.
7. Staff đẩy trạng thái → `Shipping` → `Delivered`.
8. Khách xem đơn → thấy `Delivered`.

Tiêu chí pass: trạng thái cuối — order `SHIPPED/DELIVERED`, payment `Success`, shipment
`Delivered`; ba service có dữ liệu nhất quán cho cùng `order_id`.

**Kịch bản thất bại (chứng minh nhánh lỗi):**
1–3 như trên.
4. Tạo đơn với thanh toán ép thất bại (`simulate:"fail"`).
5. payment trả `Failed` → order `PAYMENT_FAILED`.
6. Kiểm `GET shipping/status?order_id=<đơn>` → `404`, **không** có shipment.

Tiêu chí pass: payment `Failed`, đơn `PAYMENT_FAILED`, **không** tồn tại shipment. Đây là
bằng chứng cho câu "payment success → gọi shipping" của tài liệu 4.7.2.

> Khi cả hai kịch bản pass và mỗi service đều có git tag `*-ok`, bạn đã hoàn thành hệ thống
> đúng theo tài liệu — và quan trọng hơn, bạn chứng minh được nó đúng chứ không chỉ "nhìn
> thấy chạy".
