# Contract: order-service

> Cùng khung với các contract trước. order-service chạy ở **cổng 8004** (đổi nếu cần).
> Đây là service **điều phối (orchestrator)**: theo tài liệu mục 2.6.2 và 4.7.2, nó tạo đơn
> từ giỏ → gọi payment-service → khi thanh toán thành công mới gọi shipping-service.
>
> Vì payment-service và shipping-service đứng **sau** order trong luồng (mục 2.9), mục 5
> được chia 2 giai đoạn: phần chạy được ngay (chỉ cần cart + product), và phần tích hợp đầy
> đủ (chạy sau khi đã dựng payment + shipping).
>
> JWT: nhận token user-service, dùng chung khóa ký, lấy `user_id` + `role` từ token.

---

## 1. Phạm vi (Bounded Context)

order-service quản lý **đơn hàng và vòng đời đơn** (theo tài liệu 2.6):

- Tạo đơn hàng từ giỏ của người dùng (đọc cart-service).
- Tính tổng tiền dựa trên giá thật từ product-service.
- Điều phối thanh toán (gọi payment-service) rồi giao hàng (gọi shipping-service).
- Lưu và truy vấn lịch sử đơn của người dùng.

**Không** thuộc phạm vi: lưu giỏ (cart-service), xử lý giao dịch tiền (payment-service),
trạng thái vận chuyển chi tiết (shipping-service). Không đụng DB service khác.

---

## 2. Data model (bám sát tài liệu 2.6.1 / 2.10.4)

**Order** (bảng `orders`)

| Field        | Kiểu        | Ràng buộc                  | Ghi chú                              |
|--------------|-------------|----------------------------|--------------------------------------|
| id           | int         | PK, auto                   |                                      |
| user_id      | int         | bắt buộc                   | lấy từ JWT                           |
| total_price  | số tiền     | bắt buộc, >= 0             | tính từ giá product-service          |
| status       | string(50)  | trong tập trạng thái mục 3 | mặc định `PENDING`                   |

**OrderItem** (bảng `order_item`)

| Field      | Kiểu      | Ràng buộc          | Ghi chú                                |
|------------|-----------|--------------------|----------------------------------------|
| id         | int       | PK, auto           |                                        |
| order_id   | FK → Order| bắt buộc           |                                        |
| product_id | int       | bắt buộc           | tham chiếu sang product-service        |
| quantity   | int       | bắt buộc, >= 1     |                                        |

> Ghi chú (cải tiến, không bắt buộc theo tài liệu): nên thêm cột `unit_price` vào
> `order_item` để **chốt giá tại thời điểm đặt**. Nếu không, khi product-service đổi giá,
> đơn cũ sẽ tính sai. Đây là vấn đề đúng/sai nghiệp vụ — đáng cân nhắc thêm.

---

## 3. Trạng thái đơn & luật nghiệp vụ (Business Rules)

Tài liệu (2.6.2, 4.7.2) mô tả luồng: tạo từ giỏ → payment → (thành công) → shipping. Từ đó
tập trạng thái đơn:

`PENDING` (đã tạo, chờ thanh toán) → `PAID` (thanh toán thành công) → `SHIPPED` (đã chuyển
shipping) → `DELIVERED` (giao xong). Nhánh lỗi: `PAYMENT_FAILED`, `CANCELLED`.

- **BR-1**: `user_id` lấy từ JWT, không lấy từ body.
- **BR-2**: Tạo đơn = đọc giỏ của user qua cart-service. Giỏ **rỗng** → không tạo được đơn (400).
- **BR-3**: `total_price` do server tính = Σ(giá product-service × quantity). Bỏ qua mọi
  `total_price` client gửi lên (chống gian lận giá).
- **BR-4**: Kiểm lại tồn kho tại thời điểm đặt (đọc `stock` từ product-service). Nếu không đủ
  hàng → từ chối (400). (Tồn kho có thể đã đổi từ lúc thêm vào giỏ.)
- **BR-5 (cốt lõi, theo tài liệu 4.7.2)**: order-service gọi payment-service trước; **chỉ khi**
  payment trả về thành công mới gọi shipping-service. Payment thất bại → **không** tạo
  shipment, đơn chuyển `PAYMENT_FAILED`.
- **BR-6 (cách ly)**: Người dùng chỉ xem/tạo được đơn của chính mình. Không xem được đơn người khác.
- **BR-7 (nhất quán khi lỗi)**: Nếu payment-service hoặc shipping-service không phản hồi,
  không để đơn rơi vào trạng thái nửa vời. Lỗi payment → đơn vẫn `PENDING`/`PAYMENT_FAILED`,
  tuyệt đối không có shipment được tạo.
- **BR-8**: Chuyển trạng thái chỉ đi theo thứ tự hợp lệ ở trên (không nhảy từ `PENDING` thẳng
  sang `DELIVERED`).

---

## 4. API (hợp đồng với bên ngoài)

Base URL local: `http://localhost:8004`. Các URL nội bộ (Docker / chạy tay):
cart `http://cart-service:8003`, product `http://product-service:8002`,
payment `http://payment-service:8005`, shipping `http://shipping-service:8006`.

| Method | Đường dẫn       | Quyền cần | Body vào                       | Trả ra (thành công)                                  |
|--------|-----------------|-----------|--------------------------------|------------------------------------------------------|
| POST   | /orders/        | token     | `{shipping_address}`           | 201 + `{id, total_price, status, items:[...]}`       |
| GET    | /orders/        | token     | —                              | 200 + danh sách đơn của chính user                   |
| GET    | /orders/{id}    | token     | —                              | 200 + chi tiết đơn + items                           |

Luồng của `POST /orders/` (theo 2.6.2): đọc giỏ → kiểm tồn → tính tổng → tạo đơn `PENDING`
→ gọi payment → nếu thành công gọi shipping, cập nhật `SHIPPED`; nếu thất bại để `PAYMENT_FAILED`.

Mã lỗi: `400` giỏ rỗng/thiếu hàng/dữ liệu sai, `401` thiếu token, `403` không đủ quyền/đơn
người khác, `404` không thấy đơn, `503` service phụ thuộc không phản hồi.

---

## 5. Tiêu chí nghiệm thu — Test API

### Giai đoạn A — chạy được ngay (cần user + product + cart)

Trước hết, dùng `khach1` thêm vài sản phẩm vào giỏ (theo TC của cart-service). Token lấy từ
user-service.

#### TC-01 — Tạo đơn từ giỏ có hàng (BR-2, BR-3)
```bash
curl -i -X POST http://localhost:8004/orders/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address":"123 Le Loi, Ha Noi"}'
```
Mong đợi: `201`. Đơn có `items` khớp với giỏ, `total_price` = Σ(giá × số lượng) tính đúng,
`status` ban đầu là `PENDING` (hoặc kết quả sau điều phối nếu giai đoạn B đã wired).

#### TC-02 — Giỏ rỗng thì không tạo được đơn (BR-2)
Dùng `khach2` (giỏ rỗng):
```bash
curl -i -X POST http://localhost:8004/orders/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER_2>" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address":"X"}'
```
Mong đợi: `400`, báo giỏ trống. Không tạo đơn.

#### TC-03 — Tổng tiền do server tính, bỏ qua giá client gửi (BR-3) ⚠️ chống gian lận
```bash
curl -i -X POST http://localhost:8004/orders/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address":"123 Le Loi","total_price":1}'
```
Mong đợi: đơn tạo ra có `total_price` đúng theo giá thật, **không** phải 1. Server bỏ qua
trường client gửi.

#### TC-04 — user_id lấy từ token, không từ body (BR-1) ⚠️ bảo mật
```bash
curl -i -X POST http://localhost:8004/orders/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER_2>" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address":"X","user_id":1}'
```
Mong đợi: đơn (nếu tạo được) thuộc về khach2 theo token, `user_id`=1 trong body bị bỏ qua.

#### TC-05 — Không token → 401 (BR)
```bash
curl -i -X POST http://localhost:8004/orders/ -H "Content-Type: application/json" -d '{}'
```
Mong đợi: `401`.

#### TC-06 — Cách ly đơn giữa người dùng (BR-6) ⚠️ bảo mật
khach2 cố xem đơn của khach1:
```bash
# {id} là id đơn của khach1 tạo ở TC-01
curl -i http://localhost:8004/orders/1 \
  -H "Authorization: Bearer <ACCESS_CUSTOMER_2>"
```
Mong đợi: `403` (hoặc `404`). Không cho xem đơn người khác.

#### TC-07 — Kiểm tồn kho lúc đặt (BR-4) ⚠️ liên service
Giảm `stock` của sản phẩm xuống dưới số lượng trong giỏ (qua product-service, token admin),
rồi tạo đơn lại.
Mong đợi: `400`, báo không đủ hàng. Chứng tỏ order-service đọc tồn kho thật từ product-service.

> Gợi ý khi payment/shipping chưa có: cho order-service dừng ở `PENDING` sau khi tạo đơn
> (chưa wired điều phối), hoặc dùng một mock payment trả "success" để chạy thử. Giai đoạn B
> dưới đây test phần điều phối thật.

### Giai đoạn B — tích hợp đầy đủ (chạy sau khi đã dựng payment + shipping)

#### TC-08 — Luồng thành công đầu-cuối (BR-5) ⚠️ tích hợp nhiều service
Giỏ có hàng, payment-service và shipping-service đang chạy, tạo đơn như TC-01.
Mong đợi: order-service gọi payment (kết quả Success) → gọi shipping → đơn kết thúc ở
`SHIPPED`. Kiểm chéo: payment-service có bản ghi `Success`, shipping-service có shipment cho
order_id này. Đây đúng luồng tài liệu mục 4.7.2.

#### TC-09 — Thanh toán thất bại thì KHÔNG giao hàng (BR-5) ⚠️ luật cốt lõi của tài liệu
Ép payment trả `Failed` (tài khoản test, hoặc cấu hình payment trả lỗi), rồi tạo đơn.
Mong đợi: đơn ở `PAYMENT_FAILED`, shipping-service **không** có shipment nào cho order này.
Đây là kiểm chứng trực tiếp câu "payment success → gọi shipping" trong mục 4.7.2: thất bại
thì dừng.

#### TC-10 — payment-service sập thì đơn không nửa vời (BR-7) ⚠️ nhất quán
Tắt payment-service, tạo đơn.
Mong đợi: trả lỗi rõ ràng (vd `503`) trong thời gian giới hạn; đơn ở `PENDING`/`PAYMENT_FAILED`;
**không** có shipment được tạo; không có exception/500 lộ stack trace.

#### TC-11 — Không tạo đơn/charge trùng (BR, nâng cao — tùy chọn)
Gửi `POST /orders/` hai lần liên tiếp cho cùng một giỏ.
Mong đợi: không tạo hai shipment / hai lần thanh toán cho cùng nội dung (idempotency, hoặc
giỏ được dọn sau khi đặt nên lần hai báo giỏ trống).

---

## 6. Kiểm tra giao diện (UI)

> Làm sau khi mục 5 xanh. Mỗi mục gắn với một luật nghiệp vụ, có kết quả quan sát được rõ
> ràng — không phải "nhìn cho đẹp". Ghi pass/fail từng dòng.

- [ ] **U-01 (BR-2)**: Từ giỏ bấm "Đặt hàng" → tạo đơn và chuyển sang trang xác nhận hiển
  thị danh sách sản phẩm + tổng tiền.
- [ ] **U-02 (BR-2)**: Giỏ trống → nút đặt hàng bị khóa hoặc báo "giỏ trống", không cho qua bước thanh toán.
- [ ] **U-03 (BR-3)**: Tổng tiền trên trang xác nhận đúng bằng Σ thành tiền các dòng.
- [ ] **U-04 (BR-5)**: Thanh toán thành công → trạng thái đơn hiển thị "Đã thanh toán/Đang giao",
  có trang xác nhận đơn.
- [ ] **U-05 (BR-5)**: Thanh toán thất bại → UI báo lỗi rõ ràng, đơn **không** hiện "đang giao",
  có lối thử lại.
- [ ] **U-06 (BR-6)**: Trang lịch sử đơn chỉ hiện đơn của tài khoản đang đăng nhập; đổi tài
  khoản → danh sách đơn khác.
- [ ] **U-07 (BR-7)**: Service phụ thuộc lỗi giữa lúc đặt hàng → UI báo thân thiện, không
  trắng trang/treo, không mất giỏ.

---

## 7. Definition of Done (nghiệm thu xong khi)

- [ ] Giai đoạn A: TC-01 → TC-07 pass.
- [ ] Giai đoạn B: TC-08 → TC-10 pass (TC-11 nếu làm idempotency).
- [ ] UI: U-01 → U-07 pass.
- [ ] order-service đọc giỏ, giá, tồn kho qua **API** (không nối DB), có timeout cho mọi lời gọi.
- [ ] Đúng luật tài liệu 4.7.2: payment thành công mới gọi shipping (xác nhận qua TC-08/TC-09).
- [ ] `user_id` và `total_price` đều do server quyết định, không tin client (TC-03/TC-04).
- [ ] Database riêng cho order-service.
- [ ] README ghi cách chạy (cổng 8004, URL các service phụ thuộc, secret JWT).
- [ ] Đã `git commit` + `git tag order-service-ok` kèm ghi chú "đã pass TC + U".

> Xanh hết Giai đoạn A là có thể sang dựng payment-service, rồi quay lại chạy Giai đoạn B.
