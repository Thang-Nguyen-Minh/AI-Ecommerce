# Contract: product-service

> Cùng khung với contract user-service. Mục 5 (test case) là phần để bạn nghiệm thu mà
> không cần đọc code. product-service chạy ở **cổng 8002**, database **PostgreSQL**.
>
> Lưu ý quan trọng: product-service **không tự cấp token**. Nó nhận JWT do user-service
> cấp, kiểm tra chữ ký và đọc claim `role` trong token để phân quyền. ⇒ Hai service phải
> dùng **chung khóa ký JWT** (cùng `SIGNING_KEY`/secret). Nếu khác khóa, mọi test phân
> quyền bên dưới sẽ fail vì token bị coi là không hợp lệ. Đây là điểm tích hợp dễ sai nhất.

---

## 1. Phạm vi (Bounded Context)

product-service chịu trách nhiệm về **danh mục sản phẩm và tồn kho**:

- Quản lý danh mục (Category) và sản phẩm (Product).
- Lưu chi tiết theo loại: Book, Electronics, Fashion.
- Cho phép xem danh sách / chi tiết sản phẩm (công khai để khách duyệt hàng).
- Là nguồn dữ liệu mà **cart-service và order-service sẽ gọi vào** để lấy giá và tồn kho.

**Không** thuộc phạm vi: giỏ hàng, đơn hàng, thanh toán, người dùng. Không đụng DB service khác.

---

## 2. Data model (PostgreSQL)

Một Product cha + ba bảng chi tiết theo loại (quan hệ một-một, kế thừa logic).

**Category**

| Field | Kiểu        | Ràng buộc        |
|-------|-------------|------------------|
| id    | int         | PK, auto         |
| name  | string(100) | bắt buộc         |

**Product**

| Field        | Kiểu        | Ràng buộc                         | Ghi chú                       |
|--------------|-------------|-----------------------------------|-------------------------------|
| id           | int         | PK, auto                          |                               |
| name         | string(255) | bắt buộc                          |                               |
| price        | số tiền     | bắt buộc, **> 0**                 | xem ghi chú dưới bảng         |
| stock        | int         | bắt buộc, **>= 0**                | không bao giờ âm              |
| category_id  | FK → Category | bắt buộc, category phải tồn tại |                               |

**Book** (OneToOne → Product): `author`, `publisher`, `isbn`
**Electronics** (OneToOne → Product): `brand`, `warranty` (số tháng, >= 0)
**Fashion** (OneToOne → Product): `size`, `color`

> Ghi chú về `price`: tài liệu dùng `FloatField`, nhưng tiền nên dùng `DecimalField`
> (vd `max_digits=12, decimal_places=2`) để tránh sai số lẻ khi cộng giỏ hàng. Đây là
> vấn đề đúng/sai nghiệp vụ, không chỉ là code — nên ghi rõ trong contract.

---

## 3. Luật nghiệp vụ (Business Rules)

- **BR-1**: `stock >= 0`. Tạo/sửa với stock âm → từ chối (400).
- **BR-2**: `price > 0`. Giá <= 0 → từ chối (400).
- **BR-3**: `category_id` phải trỏ tới một Category đang tồn tại. Category không tồn tại → 400.
- **BR-4**: Mỗi Product chỉ gắn **một** bản ghi chi tiết loại (OneToOne). Không cho tạo 2
  Book cho cùng một Product.
- **BR-5**: Một Product thuộc đúng **một** loại trong {Book, Electronics, Fashion}.
- **BR-6 (RBAC)** — đọc role từ JWT của user-service:

  | Hành động                              | ẩn danh | customer | staff | admin |
  |----------------------------------------|:-------:|:--------:|:-----:|:-----:|
  | Xem danh sách / chi tiết sản phẩm      |   ✅    |    ✅    |  ✅   |  ✅   |
  | Tạo / sửa / xóa sản phẩm, danh mục     |   ❌    |    ❌    |  ✅   |  ✅   |

- **BR-7**: GET là công khai (không cần token) để khách duyệt hàng. Mọi thao tác ghi
  (POST/PUT/PATCH/DELETE) bắt buộc token và role ∈ {staff, admin}.

---

## 4. API (hợp đồng với bên ngoài)

Base URL khi chạy local: `http://localhost:8002`

| Method | Đường dẫn         | Quyền cần   | Body vào                                              | Trả ra (thành công)                         |
|--------|-------------------|-------------|-------------------------------------------------------|---------------------------------------------|
| GET    | /categories/      | công khai   | —                                                     | 200 + `[{id, name}, ...]`                   |
| POST   | /categories/      | staff/admin | `{name}`                                              | 201 + `{id, name}`                          |
| GET    | /products/        | công khai   | (query `?category=<id>` tùy chọn)                     | 200 + `[{id, name, price, stock, category}]`|
| GET    | /products/{id}    | công khai   | —                                                     | 200 + product kèm chi tiết loại             |
| POST   | /products/        | staff/admin | `{name, price, stock, category_id, type, detail{...}}`| 201 + product vừa tạo                       |
| PATCH  | /products/{id}    | staff/admin | trường cần sửa, vd `{stock}`                          | 200 + product sau khi sửa                   |
| DELETE | /products/{id}    | staff/admin | —                                                     | 204                                         |

Quy ước mã lỗi: `400` dữ liệu sai/vi phạm ràng buộc, `401` thiếu/sai token, `403` token
đúng nhưng không đủ quyền, `404` không tìm thấy.

> Lưu ý hợp đồng liên service: cart-service/order-service sẽ gọi `GET /products/{id}` để
> lấy `price` và `stock`. ⇒ Hai trường này phải luôn có trong response chi tiết. Đổi tên
> chúng = phá hợp đồng với service khác.

---

## 5. Tiêu chí nghiệm thu — Test case (chạy được ngay)

Token lấy từ user-service (xem TC-04/TC-08 của contract user-service). Thay
`<ACCESS_ADMIN>` và `<ACCESS_CUSTOMER>` bằng chuỗi `access` tương ứng.

### TC-01 — Tạo category (staff/admin) (BR-6)
```bash
curl -i -X POST http://localhost:8002/categories/ \
  -H "Authorization: Bearer <ACCESS_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sach"}'
```
Mong đợi: `201`, body có `id` và `name`. Nhớ `id` này để dùng cho TC sau.

### TC-02 — Tạo sản phẩm hợp lệ (staff/admin)
```bash
curl -i -X POST http://localhost:8002/products/ \
  -H "Authorization: Bearer <ACCESS_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Lap trinh Python","price":120000,"stock":10,"category_id":1,
       "type":"book","detail":{"author":"A. Nguyen","publisher":"NXB X","isbn":"978-0000000000"}}'
```
Mong đợi: `201`. Body trả về có cả phần chi tiết Book (author, isbn).

### TC-03 — Customer KHÔNG được tạo sản phẩm (BR-6) ⚠️ case nghiệp vụ cốt lõi
```bash
curl -i -X POST http://localhost:8002/products/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hang lau","price":1000,"stock":1,"category_id":1,"type":"book","detail":{}}'
```
Mong đợi: `403`. Token hợp lệ nhưng role customer không đủ quyền ghi.

### TC-04 — Không token thì không tạo được (BR-7)
```bash
curl -i -X POST http://localhost:8002/products/ \
  -H "Content-Type: application/json" \
  -d '{"name":"X","price":1000,"stock":1,"category_id":1,"type":"book","detail":{}}'
```
Mong đợi: `401`.

### TC-05 — Stock âm bị chặn (BR-1)
```bash
curl -i -X POST http://localhost:8002/products/ \
  -H "Authorization: Bearer <ACCESS_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sai stock","price":1000,"stock":-5,"category_id":1,"type":"book","detail":{}}'
```
Mong đợi: `400`, báo lỗi về stock.

### TC-06 — Giá <= 0 bị chặn (BR-2)
```bash
curl -i -X POST http://localhost:8002/products/ \
  -H "Authorization: Bearer <ACCESS_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sai gia","price":0,"stock":5,"category_id":1,"type":"book","detail":{}}'
```
Mong đợi: `400`, báo lỗi về price.

### TC-07 — Category không tồn tại bị chặn (BR-3)
```bash
curl -i -X POST http://localhost:8002/products/ \
  -H "Authorization: Bearer <ACCESS_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Cat sai","price":1000,"stock":5,"category_id":99999,"type":"book","detail":{}}'
```
Mong đợi: `400` (hoặc 404), báo category không tồn tại. Không tạo ra product mồ côi.

### TC-08 — Xem danh sách công khai, không cần token (BR-7)
```bash
curl -i http://localhost:8002/products/
```
Mong đợi: `200`, trả về mảng sản phẩm.

### TC-09 — Chi tiết sản phẩm có kèm price + stock (hợp đồng liên service)
```bash
# Thay {id} bằng id sản phẩm tạo ở TC-02
curl -i http://localhost:8002/products/1
```
Mong đợi: `200`. Body **có** trường `price` và `stock` (cart/order-service phụ thuộc vào
đây), và có phần chi tiết theo loại (author/isbn với sách).

### TC-10 — Không gắn 2 chi tiết loại cho cùng 1 product (BR-4)
Thử tạo thêm một Book trỏ vào product đã có Book (qua endpoint tạo Book trực tiếp nếu có,
hoặc gửi lại type=book cho cùng product_id).
Mong đợi: bị từ chối (`400`). Một product chỉ có một bản ghi chi tiết loại.

### TC-11 — Customer vẫn xem được sản phẩm (BR-6)
```bash
curl -i http://localhost:8002/products/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>"
```
Mong đợi: `200`. Quyền đọc không bị chặn với customer.

---

## 6. Definition of Done (nghiệm thu xong khi)

- [ ] TC-01 → TC-11 đều pass.
- [ ] Dùng database PostgreSQL **riêng** cho product-service, không đụng DB service khác.
- [ ] Dùng **chung khóa ký JWT** với user-service (đã xác nhận qua TC-03/TC-04 chạy đúng).
- [ ] Response chi tiết luôn có `price` và `stock` (hợp đồng cho cart/order).
- [ ] Có README ghi cách chạy (cổng 8002, biến môi trường DB, secret JWT).
- [ ] Đã `git commit` + `git tag product-service-ok` kèm ghi chú "đã pass TC-01..11".

> Xanh hết mới sang cart-service. cart-service sẽ dựa trên hợp đồng `GET /products/{id}`
> ở đây, nên product-service phải chắc trước.
