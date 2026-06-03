# Contract: cart-service

> Cùng khung với contract trước. cart-service chạy ở **cổng 8003** (đổi nếu cần). Đây là
> service đầu tiên **gọi sang product-service** (lấy giá, kiểm tồn kho khi thêm vào giỏ),
> nên có thêm mục test giao tiếp liên service. Mục 6 là kiểm tra giao diện (UI) — làm
> **sau khi** mục 5 (API) đã pass.
>
> JWT: cart-service nhận token do user-service cấp, dùng **chung khóa ký** để xác thực và
> lấy `user_id` + `role` từ token. Tuyệt đối không lấy `user_id` từ body request.

---

## 1. Phạm vi (Bounded Context)

cart-service quản lý **giỏ hàng của từng người dùng**:

- Thêm sản phẩm vào giỏ, cập nhật số lượng, xóa sản phẩm.
- Xem giỏ hàng hiện tại của chính mình.
- Khi thêm hàng, **gọi product-service** để xác minh sản phẩm tồn tại, lấy giá và kiểm tồn kho.

**Không** thuộc phạm vi: tạo sản phẩm (của product-service), tạo đơn hàng (của order-service).
order-service sau này sẽ đọc giỏ từ đây để tạo đơn. Không đụng DB service khác.

---

## 2. Data model (database riêng)

**Cart**

| Field   | Kiểu | Ràng buộc            | Ghi chú                          |
|---------|------|----------------------|----------------------------------|
| id      | int  | PK, auto             |                                  |
| user_id | int  | bắt buộc, **duy nhất**| mỗi user một giỏ; lấy từ JWT     |

**CartItem**

| Field      | Kiểu | Ràng buộc                          | Ghi chú                                   |
|------------|------|------------------------------------|-------------------------------------------|
| id         | int  | PK, auto                           |                                           |
| cart_id    | FK → Cart | bắt buộc                      |                                           |
| product_id | int  | bắt buộc                           | tham chiếu sang product-service (không FK)|
| quantity   | int  | bắt buộc, **>= 1**                 |                                           |

> `product_id` chỉ là số tham chiếu — cart-service **không** có bảng product và **không**
> nối DB sang product-service. Muốn biết sản phẩm có thật, giá, tồn kho thì gọi API.

---

## 3. Luật nghiệp vụ (Business Rules)

- **BR-1**: Mỗi user có đúng một giỏ. `user_id` luôn lấy từ JWT, không lấy từ body.
- **BR-2**: Khi thêm hàng, gọi `GET product-service /products/{id}`. Nếu sản phẩm không tồn
  tại (product-service trả 404) → từ chối thêm.
- **BR-3**: `quantity >= 1`. Thêm/sửa với số lượng 0 hoặc âm → từ chối (400).
- **BR-4**: Tổng số lượng của một sản phẩm trong giỏ **không vượt tồn kho** (`stock` đọc từ
  product-service). Vượt → từ chối (400).
- **BR-5**: Thêm lại sản phẩm đã có trong giỏ → **cộng dồn** vào dòng cũ, không tạo dòng trùng.
- **BR-6 (cách ly giỏ)**: Một user chỉ xem/sửa được giỏ của **chính mình**. Không có cách nào
  đọc/sửa giỏ người khác, kể cả khi cố truyền `user_id` khác trong request.
- **BR-7**: Mọi endpoint giỏ hàng đều **bắt buộc token** (khách vãng lai chưa đăng nhập không
  có giỏ ở phía server).
- **BR-8 (chịu lỗi)**: Nếu product-service không phản hồi (timeout/sập), cart-service không
  được treo hay sập — trả lỗi rõ ràng (vd 503) trong thời gian giới hạn (timeout).

---

## 4. API (hợp đồng với bên ngoài)

Base URL local: `http://localhost:8003`. Gọi nội bộ tới product-service:
`http://product-service:8002` (trong Docker) hoặc `http://localhost:8002` (chạy tay).

| Method | Đường dẫn        | Quyền cần | Body vào                  | Trả ra (thành công)                                  |
|--------|------------------|-----------|---------------------------|------------------------------------------------------|
| GET    | /cart/           | token     | —                         | 200 + `{user_id, items:[{product_id, quantity, ...}]}`|
| POST   | /cart/add        | token     | `{product_id, quantity}`  | 201/200 + giỏ sau khi thêm                           |
| PATCH  | /cart/update     | token     | `{product_id, quantity}`  | 200 + giỏ sau khi sửa                                |
| DELETE | /cart/remove     | token     | `{product_id}`            | 200 + giỏ sau khi xóa                                |

Mã lỗi: `400` dữ liệu sai/vượt tồn/sản phẩm không tồn tại, `401` thiếu/sai token, `503`
product-service không phản hồi.

> Hợp đồng cho order-service: `GET /cart/` phải trả danh sách `items` với `product_id` và
> `quantity` để order-service dựng đơn. Đừng đổi cấu trúc này.

---

## 5. Tiêu chí nghiệm thu — Test API (chạy được ngay)

Cần product-service đang chạy ở 8002 và đã có sản phẩm (tạo ở TC-02 của product-service,
giả sử là `product_id = 1`, stock = 10). Token lấy từ user-service.

### TC-01 — Thêm sản phẩm hợp lệ vào giỏ (BR-1, BR-2)
```bash
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":2}'
```
Mong đợi: `201`/`200`, giỏ có dòng product_id=1, quantity=2.

### TC-02 — Thêm sản phẩm KHÔNG tồn tại → bị chặn (BR-2) ⚠️ test liên service
```bash
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":99999,"quantity":1}'
```
Mong đợi: `400`/`404`. Đây là bằng chứng cart-service thực sự **gọi sang** product-service
và xử lý đúng khi nhận 404 — không phải tự bịa.

### TC-03 — Số lượng 0/âm bị chặn (BR-3)
```bash
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":0}'
```
Mong đợi: `400`.

### TC-04 — Vượt tồn kho bị chặn (BR-4) ⚠️ test liên service
```bash
# Sản phẩm 1 chỉ có stock=10, thử thêm 999
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":999}'
```
Mong đợi: `400`, báo vượt tồn kho. Chứng tỏ cart-service đọc `stock` từ product-service.

### TC-05 — Thêm lại thì cộng dồn, không tạo dòng trùng (BR-5)
```bash
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":1}'
```
Mong đợi: giỏ vẫn chỉ có **một** dòng cho product_id=1, quantity = 3 (2 từ TC-01 + 1).

### TC-06 — Không token thì không thao tác được (BR-7)
```bash
curl -i http://localhost:8003/cart/
```
Mong đợi: `401`.

### TC-07 — Xem đúng giỏ của mình (BR-1)
```bash
curl -i http://localhost:8003/cart/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>"
```
Mong đợi: `200`, trả giỏ của chính user trong token, có dòng product_id=1.

### TC-08 — Cách ly giỏ giữa người dùng (BR-6) ⚠️ case bảo mật
Đăng ký + login một customer thứ hai (vd `khach2`) ở user-service, lấy token của họ rồi:
```bash
curl -i http://localhost:8003/cart/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER_2>"
```
Mong đợi: `200` nhưng giỏ **rỗng** — không thấy sản phẩm của khach1.

### TC-09 — Không cho thao tác giỏ người khác qua body (BR-6) ⚠️ case bảo mật
```bash
# Cố ý nhét user_id của người khác vào body
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER_2>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"product_id":1,"quantity":1}'
```
Mong đợi: hệ thống **bỏ qua** `user_id` trong body, chỉ thêm vào giỏ của khach2 (lấy từ
token). Giỏ của khach1 không bị đụng tới.

### TC-10 — Xóa sản phẩm khỏi giỏ (BR-?)
```bash
curl -i -X DELETE http://localhost:8003/cart/remove \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1}'
```
Mong đợi: `200`, giỏ của khach1 không còn product_id=1.

### TC-11 — product-service sập thì cart không sập (BR-8) ⚠️ test chịu lỗi
Tắt product-service (dừng container/tiến trình), rồi:
```bash
curl -i -X POST http://localhost:8003/cart/add \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":1}'
```
Mong đợi: trả lỗi rõ ràng (vd `503`) trong vài giây, **không** treo vô hạn, không trả 500
kèm stack trace. Sau đó bật lại product-service để chạy tiếp các test khác.

---

## 6. Kiểm tra giao diện (UI)

> Làm **sau khi** mục 5 đã xanh. Mỗi mục là một hành vi quan sát được, gắn với một luật
> nghiệp vụ ở trên — không phải "nhìn xem có đẹp không". Ghi pass/fail từng dòng.
> Cách làm: mở web, đăng nhập bằng tài khoản thật, thao tác và quan sát kết quả.

- [ ] **U-01 (BR-1)**: Bấm "Thêm vào giỏ" ở một sản phẩm → biểu tượng giỏ tăng số, sản phẩm
  xuất hiện trong trang giỏ hàng.
- [ ] **U-02 (BR-4)**: Thêm số lượng vượt tồn kho → UI hiện thông báo lỗi rõ ràng và **không**
  thêm vào giỏ (không âm thầm thêm rồi để lỗi ở bước thanh toán).
- [ ] **U-03 (BR-3)**: Ô nhập số lượng không cho nhập 0, số âm, hoặc chữ; có chặn ở phía giao diện.
- [ ] **U-04 (tính toán)**: Tăng/giảm số lượng → thành tiền từng dòng và tổng tiền giỏ cập
  nhật ngay và đúng (tự nhân lại, không hiển thị tổng cũ).
- [ ] **U-05 (TC-10)**: Bấm xóa một sản phẩm → sản phẩm biến mất khỏi giỏ và tổng tiền giảm tương ứng.
- [ ] **U-06**: Giỏ rỗng → hiện trạng thái "giỏ hàng trống" + lối quay lại mua sắm, không
  hiện tổng tiền lỗi hay khoảng trắng vỡ layout.
- [ ] **U-07 (BR-6)**: Đăng xuất, đăng nhập tài khoản khác → giỏ hàng hiển thị **nội dung khác**,
  không lẫn sản phẩm của tài khoản trước.
- [ ] **U-08 (BR-7)**: Chưa đăng nhập mà bấm "Thêm vào giỏ" → được chuyển tới trang đăng nhập
  (hoặc báo cần đăng nhập), **không** trắng trang/đứng hình.
- [ ] **U-09 (BR-8)**: Khi product-service chậm/lỗi → UI hiện thông báo thân thiện ("không tải
  được sản phẩm, thử lại"), không treo nút bấm hay xoay vòng vô hạn.

> Mẹo: U-02, U-07, U-08, U-09 đúng là những lỗi mà cách test cũ ("nhìn giao diện") hay bỏ
> sót, vì chúng chỉ lộ ra khi đi đúng kịch bản. Có checklist thì không trôi mất.

---

## 7. Definition of Done (nghiệm thu xong khi)

- [ ] TC-01 → TC-11 (API) đều pass.
- [ ] U-01 → U-09 (UI) đều pass.
- [ ] cart-service gọi product-service qua **API** (không nối DB), có timeout cho lời gọi.
- [ ] `user_id` luôn lấy từ JWT, không từ body (đã xác nhận qua TC-09).
- [ ] Database riêng cho cart-service.
- [ ] Có README ghi cách chạy (cổng 8003, URL product-service, secret JWT).
- [ ] Đã `git commit` + `git tag cart-service-ok` kèm ghi chú "đã pass TC-01..11, U-01..09".

> Xanh hết mới sang order-service. order-service sẽ đọc `GET /cart/` ở đây để dựng đơn,
> nên cart phải chắc trước.
