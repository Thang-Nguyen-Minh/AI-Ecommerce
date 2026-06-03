# Contract: user-service

> Đây là "đề bài" bạn giao cho AI **trước khi** nó viết code, và là "đáp án" bạn dùng để
> nghiệm thu **sau khi** nó viết xong. Mục 5 (test case) là phần quan trọng nhất —
> bạn chạy được nó mà không cần đọc một dòng code nào.
>
> Cách tái sử dụng cho service khác: xem mục 7 ở cuối.

---

## 1. Phạm vi (Bounded Context)

user-service chỉ chịu trách nhiệm về **danh tính và phân quyền**:

- Đăng ký, đăng nhập, cấp JWT.
- Lưu thông tin người dùng và vai trò (role).
- Trả lời câu hỏi của các service khác: "token này hợp lệ không, người này role gì?"

**Không** thuộc phạm vi: giỏ hàng, đơn hàng, sản phẩm. user-service không được đụng vào
database của service khác (nguyên tắc database-per-service).

---

## 2. Data model

Một bảng chính. `AbstractUser` của Django đã có sẵn `username`, `password`, `email`,
`is_active`, `date_joined` — chỉ thêm `role`.

| Field        | Kiểu          | Ràng buộc                                  | Ghi chú                          |
|--------------|---------------|--------------------------------------------|----------------------------------|
| id           | int           | PK, auto                                   |                                  |
| username     | string(150)   | unique, bắt buộc                           | Không cho trùng                  |
| password     | string        | bắt buộc, **lưu dạng băm**                 | Không bao giờ lưu/trả plaintext  |
| email        | string        | tuỳ chọn                                   |                                  |
| role         | string(20)    | trong {admin, staff, customer}             | Mặc định = customer              |
| is_active    | bool          | mặc định true                              |                                  |
| date_joined  | datetime      | auto                                       |                                  |

---

## 3. Luật nghiệp vụ (Business Rules)

Đây là phần bug hay nấp. Liệt kê rõ để AI không tự ý làm khác và để bạn biết phải test gì.

- **BR-1**: Người dùng tự đăng ký qua `/auth/register` **luôn** được gán `role = customer`.
  Không cho client tự chọn `role = admin` hay `staff` qua endpoint công khai. (Đây là lỗ
  hổng leo thang quyền rất phổ biến — bắt buộc test.)
- **BR-2**: Chỉ **admin** mới được tạo tài khoản `staff` hoặc `admin` (qua endpoint quản trị
  riêng, có kèm token admin).
- **BR-3**: Password phải được băm (hash) trước khi lưu. Không endpoint nào được trả password
  về cho client.
- **BR-4**: `username` là duy nhất. Đăng ký trùng username → từ chối.
- **BR-5**: JWT trả về khi login phải chứa claim `role` (để service khác đọc quyền mà không
  phải gọi lại user-service).
- **BR-6**: Ma trận phân quyền (RBAC):

  | Hành động                         | admin | staff | customer |
  |-----------------------------------|:-----:|:-----:|:--------:|
  | Xem danh sách toàn bộ user        |  ✅   |  ❌   |    ❌    |
  | Xem hồ sơ của chính mình          |  ✅   |  ✅   |    ✅    |
  | Tạo tài khoản staff/admin         |  ✅   |  ❌   |    ❌    |
  | Mua hàng, xem sản phẩm            |  ✅   |  ✅   |    ✅    |

---

## 4. API (hợp đồng với bên ngoài)

Base URL khi chạy local: `http://localhost:8001`

| Method | Đường dẫn         | Quyền cần   | Body vào                         | Trả ra (thành công)                  |
|--------|-------------------|-------------|----------------------------------|--------------------------------------|
| POST   | /auth/register    | công khai   | `{username, password, email?}`   | 201 + `{id, username, role}`         |
| POST   | /auth/login       | công khai   | `{username, password}`           | 200 + `{access, refresh}` (JWT)      |
| GET    | /auth/me          | token bất kỳ| —                                | 200 + `{id, username, role}`         |
| GET    | /users/           | admin       | —                                | 200 + `[{id, username, role}, ...]`  |
| POST   | /users/           | admin       | `{username, password, role}`     | 201 + `{id, username, role}`         |

Quy ước mã lỗi: `400` dữ liệu sai/trùng, `401` không có/sai token, `403` token đúng nhưng
không đủ quyền, `404` không tìm thấy.

---

## 5. Tiêu chí nghiệm thu — Test case (chạy được ngay)

Chạy bằng `curl` trong terminal, hoặc dán vào Postman. Mỗi case có **kết quả mong đợi** rõ
ràng — đối chiếu là biết pass/fail, không cần đọc code.

> Gợi ý: chạy lần lượt từ trên xuống. Một số case dùng token lấy từ case trước.

### TC-01 — Đăng ký tạo đúng user (BR-1, BR-3)
```bash
curl -i -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"khach1","password":"MatKhau123!","email":"k1@test.com"}'
```
Mong đợi: status `201`. Body chứa `"role": "customer"`. Body **không** chứa trường password.

### TC-02 — Không cho tự đăng ký thành admin (BR-1) ⚠️ case bảo mật
```bash
curl -i -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"haker","password":"x123456!","role":"admin"}'
```
Mong đợi: tài khoản tạo ra vẫn là `customer` (role bị bỏ qua), HOẶC bị từ chối. **Tuyệt đối
không** được tạo ra một admin. Nếu kết quả là admin → fail, bắt AI sửa.

### TC-03 — Username trùng bị từ chối (BR-4)
```bash
curl -i -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"khach1","password":"khac123!"}'
```
Mong đợi: status `400`, có thông báo username đã tồn tại.

### TC-04 — Login đúng trả JWT (BR-5)
```bash
curl -i -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"khach1","password":"MatKhau123!"}'
```
Mong đợi: status `200`, body có `access` và `refresh`. Copy chuỗi `access` ra để dùng tiếp.

Kiểm tra token có chứa role: dán chuỗi `access` vào https://jwt.io và xem phần payload có
`"role": "customer"` không. (Không cần đọc code, chỉ cần dán.)

### TC-05 — Login sai mật khẩu bị chặn
```bash
curl -i -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"khach1","password":"SAI_HET"}'
```
Mong đợi: status `401`. Không trả token.

### TC-06 — Không có token thì không vào được (BR-6)
```bash
curl -i http://localhost:8001/users/
```
Mong đợi: status `401`.

### TC-07 — Customer không được xem danh sách user (BR-6) ⚠️ case nghiệp vụ cốt lõi
```bash
# Thay <ACCESS_CUSTOMER> bằng token lấy ở TC-04
curl -i http://localhost:8001/users/ \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>"
```
Mong đợi: status `403`. Token hợp lệ nhưng không đủ quyền.

### TC-08 — Admin xem được danh sách user (BR-6)
Trước hết tạo 1 admin (dùng lệnh `python manage.py createsuperuser` rồi gán role=admin,
hoặc nhờ AI cung cấp lệnh seed admin), login lấy token admin, rồi:
```bash
# Thay <ACCESS_ADMIN> bằng token của tài khoản admin
curl -i http://localhost:8001/users/ \
  -H "Authorization: Bearer <ACCESS_ADMIN>"
```
Mong đợi: status `200`, trả về mảng danh sách user.

### TC-09 — Kiểm tra password được băm (BR-3)
Cách nhanh không cần đọc code — vào Django shell:
```bash
python manage.py shell -c "from users.models import User; print(User.objects.get(username='khach1').password)"
```
Mong đợi: chuỗi in ra bắt đầu bằng `pbkdf2_sha256$...` (hoặc `argon2$...`), **không phải**
`MatKhau123!`. Nếu thấy mật khẩu gốc → fail nghiêm trọng, bắt AI sửa ngay.

---

## 6. Definition of Done (nghiệm thu xong khi)

- [ ] Tất cả TC-01 → TC-09 đều pass.
- [ ] Có database riêng cho user-service, không đụng DB service khác.
- [ ] Có README ghi cách chạy service (lệnh, port).
- [ ] Đã `git commit` + `git tag user-service-ok` và ghi chú "đã pass TC-01..09".

> Chỉ khi mục này xanh hết mới được chuyển sang service kế tiếp.

---

## 7. Cách dùng file này làm mẫu cho service khác

Giữ nguyên 6 mục trên, chỉ thay nội dung. Khi làm product-service / cart-service / ... bạn
copy file này rồi sửa:

1. **Phạm vi**: đổi sang đúng bounded context (vd product-service quản lý sản phẩm + danh mục).
2. **Data model**: đổi bảng (vd Product, Category, Book, Electronics, Fashion).
3. **Luật nghiệp vụ**: viết lại các BR (vd "chỉ admin/staff được tạo sản phẩm", "stock không
   được âm").
4. **API**: liệt kê endpoint mới.
5. **Test case**: mỗi luật nghiệp vụ → ít nhất 1 case curl có input + kết quả mong đợi.
6. **Definition of Done + git tag** đổi tên service.

Mẹo giao việc cho AI: đưa cả file này và nói *"Build service đúng theo contract này, rồi
đưa lại cho tôi các lệnh curl để tự chạy từng test case ở mục 5."* — AI vừa code vừa đưa
bạn công cụ nghiệm thu.
