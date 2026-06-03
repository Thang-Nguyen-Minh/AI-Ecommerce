# Contract: payment-service

> Cùng khung với các contract trước. payment-service chạy ở **cổng 8005** (đổi nếu cần).
> Bám sát tài liệu mục 2.7: model `Payment(order_id, amount, status)`, trạng thái
> Pending/Success/Failed, API `/payment/pay` và `/payment/status`.
>
> payment-service được **order-service gọi tới** (server-to-server), không phải khách hàng
> gọi trực tiếp. Kết quả của nó (Success/Failed) chính là thứ order-service dùng để quyết
> định có gọi shipping hay không (tài liệu 4.7.2).

---

## 1. Phạm vi (Bounded Context)

payment-service quản lý **giao dịch thanh toán cho đơn hàng** (tài liệu 2.7):

- Nhận yêu cầu thanh toán cho một `order_id` với một `amount`.
- Tạo bản ghi Payment, xử lý (qua cổng thanh toán/sandbox), trả về trạng thái.
- Cho truy vấn trạng thái thanh toán theo đơn.

**Không** thuộc phạm vi: tạo đơn (order-service), giao hàng (shipping-service), tính tổng
tiền (do order-service tính rồi gửi sang). Không đụng DB service khác.

---

## 2. Data model (bám sát tài liệu 2.7.1 / 2.10.4)

**Payment** (bảng `payment`)

| Field    | Kiểu        | Ràng buộc                     | Ghi chú                          |
|----------|-------------|-------------------------------|----------------------------------|
| id       | int         | PK, auto                      |                                  |
| order_id | int         | bắt buộc                      | tham chiếu sang order-service    |
| amount   | số tiền     | bắt buộc, **> 0**             | do order-service gửi sang        |
| status   | string(50)  | trong {Pending, Success, Failed} | mặc định `Pending`            |

> Ghi chú (cải tiến): nên đặt `order_id` là **unique** (mỗi đơn một giao dịch hợp lệ) và
> thêm `created_at`. Giúp chống thanh toán trùng (xem BR-3). Tài liệu không bắt buộc, nhưng
> đây là vấn đề đúng/sai nghiệp vụ về tiền nên đáng làm.

---

## 3. Trạng thái & luật nghiệp vụ (Business Rules)

Trạng thái theo tài liệu 2.7.2: `Pending` → `Success` **hoặc** `Failed`. Success/Failed là
trạng thái cuối (terminal).

- **BR-1**: Mỗi giao dịch gắn với một `order_id`. `amount` lấy từ yêu cầu của order-service
  (đã được order-service tính, không tin client cuối).
- **BR-2**: `amount > 0`. Số tiền <= 0 → từ chối (400).
- **BR-3 (chống charge trùng)**: Nếu một `order_id` đã có giao dịch `Success`, yêu cầu thanh
  toán lại cho đơn đó **không** tạo giao dịch mới — trả lại kết quả cũ. Tránh thu tiền hai lần.
- **BR-4 (nội bộ)**: `/payment/pay` chỉ được gọi từ order-service (nội bộ), **không** lộ ra
  cho khách hàng qua API Gateway. Nếu lộ, khách có thể tự gọi để đánh dấu đơn đã trả mà không
  trả tiền.
- **BR-5**: Trạng thái cuối không đổi. Đã `Success` thì không chuyển về `Failed` và ngược lại.
- **BR-6 (sandbox để test nhánh lỗi)**: Ở môi trường dev (biến môi trường `PAYMENT_SANDBOX=true`),
  payment-service hỗ trợ điều khiển kết quả để test: kết quả mặc định là `Success`, nhưng khi
  yêu cầu kèm cờ thử nghiệm (vd `simulate: "fail"`) thì trả `Failed`. Ở môi trường thật, cờ này
  bị bỏ qua. Đây là điều kiện để chạy được TC-09 của order-service.

---

## 4. API (hợp đồng với bên ngoài)

Base URL nội bộ: `http://payment-service:8005` (Docker) hoặc `http://localhost:8005` (chạy tay).
Không định tuyến công khai qua gateway (BR-4).

| Method | Đường dẫn         | Quyền cần        | Body / Query                          | Trả ra (thành công)                       |
|--------|-------------------|------------------|----------------------------------------|-------------------------------------------|
| POST   | /payment/pay      | nội bộ (order)   | `{order_id, amount, simulate?}`        | 201 + `{id, order_id, amount, status}`    |
| GET    | /payment/status   | nội bộ (order)   | `?order_id=<id>`                       | 200 + `{order_id, status}`                |

Mã lỗi: `400` amount sai/thiếu dữ liệu, `404` không có giao dịch cho order_id (khi query),
`422` (tùy chọn) khi xử lý thanh toán bị từ chối.

> Hợp đồng cho order-service: response của `/payment/pay` phải có trường `status` nhận đúng
> một trong ba giá trị `Pending|Success|Failed`. order-service đọc đúng trường này để quyết
> định gọi shipping hay không. Đổi tên/giá trị = phá luồng 4.7.2.

---

## 5. Tiêu chí nghiệm thu — Test API

Các test này không cần token người dùng (đây là endpoint nội bộ). Chạy trực tiếp tới cổng 8005.

### TC-01 — Thanh toán hợp lệ trả Success (BR-1, sandbox happy path)
```bash
curl -i -X POST http://localhost:8005/payment/pay \
  -H "Content-Type: application/json" \
  -d '{"order_id":1,"amount":240000}'
```
Mong đợi: `201`, body có `status: "Success"`, tạo một bản ghi Payment cho order_id=1.

### TC-02 — Số tiền <= 0 bị chặn (BR-2)
```bash
curl -i -X POST http://localhost:8005/payment/pay \
  -H "Content-Type: application/json" \
  -d '{"order_id":2,"amount":0}'
```
Mong đợi: `400`, báo lỗi amount. Không tạo giao dịch.

### TC-03 — Truy vấn trạng thái theo đơn (tài liệu 2.7.3)
```bash
curl -i "http://localhost:8005/payment/status?order_id=1"
```
Mong đợi: `200`, trả `{order_id: 1, status: "Success"}` khớp với TC-01.

### TC-04 — Không thu tiền hai lần cho cùng một đơn (BR-3) ⚠️ nghiệp vụ tiền
Gọi lại y hệt TC-01 cho order_id=1:
```bash
curl -i -X POST http://localhost:8005/payment/pay \
  -H "Content-Type: application/json" \
  -d '{"order_id":1,"amount":240000}'
```
Mong đợi: **không** tạo giao dịch Success thứ hai. Trả lại kết quả cũ (vd `200` + giao dịch
đã có). Kiểm tra trong DB chỉ có một bản ghi Success cho order_id=1.

### TC-05 — Ép thất bại để test nhánh lỗi (BR-6) ⚠️ điều kiện cho order TC-09
```bash
curl -i -X POST http://localhost:8005/payment/pay \
  -H "Content-Type: application/json" \
  -d '{"order_id":3,"amount":100000,"simulate":"fail"}'
```
Mong đợi (khi `PAYMENT_SANDBOX=true`): `status: "Failed"`. Đây là cách order-service tạo được
kịch bản thanh toán hỏng để kiểm chứng "thất bại thì không giao hàng".

### TC-06 — Trạng thái cuối không bị ghi đè (BR-5)
Sau khi order_id=1 đã `Success`, thử ép nó thành fail:
```bash
curl -i -X POST http://localhost:8005/payment/pay \
  -H "Content-Type: application/json" \
  -d '{"order_id":1,"amount":240000,"simulate":"fail"}'
```
Mong đợi: order_id=1 vẫn `Success`, không bị đổi sang Failed.

### TC-07 — Endpoint nội bộ không lộ ra ngoài (BR-4) ⚠️ bảo mật
Nếu đã có API Gateway: thử gọi `/payment/pay` qua URL công khai của gateway bằng token khách
hàng.
```bash
# Ví dụ qua gateway công khai (không phải cổng nội bộ 8005)
curl -i -X POST http://localhost/payment/pay \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"order_id":1,"amount":1}'
```
Mong đợi: `404`/`403` — gateway không định tuyến endpoint thanh toán cho khách. (Nếu chưa
dựng gateway, ghi đây là yêu cầu cấu hình cần làm khi dựng gateway ở chương 4.)

---

## 6. Kiểm tra giao diện (UI)

> payment-service không có giao diện riêng (là service nội bộ). Bước thanh toán xuất hiện
> trong luồng checkout do order-service điều phối. Các kiểm tra UI dưới đây quan sát đúng
> khoảnh khắc thanh toán trong giao diện checkout. Làm sau khi mục 5 xanh.

- [ ] **U-01 (BR-6, happy path)**: Bấm thanh toán ở bước checkout → hiện trạng thái "đang xử
  lý" rồi chuyển sang màn hình thành công; đơn hiển thị đã thanh toán.
- [ ] **U-02 (BR-6, nhánh lỗi)**: Khi thanh toán thất bại → UI báo lỗi rõ ràng ("thanh toán
  không thành công"), **không** chuyển sang trạng thái đã giao, có nút thử lại.
- [ ] **U-03 (BR-3)**: Bấm nút thanh toán hai lần (hoặc tải lại trang giữa chừng) → không bị
  trừ tiền/đặt hàng hai lần.
- [ ] **U-04**: Trong lúc đang xử lý thanh toán, nút bấm bị khóa để tránh bấm liên tục; không
  treo vô hạn nếu xử lý lâu.

---

## 7. Definition of Done (nghiệm thu xong khi)

- [ ] TC-01 → TC-06 pass; TC-07 pass (hoặc ghi nhận là yêu cầu cấu hình gateway).
- [ ] UI U-01 → U-04 pass.
- [ ] Trạng thái đúng tập tài liệu 2.7.2: chỉ Pending/Success/Failed, terminal không đổi.
- [ ] Response `/payment/pay` luôn có trường `status` để order-service đọc (hợp đồng 4.7.2).
- [ ] Có sandbox ép Failed ở dev để order TC-09 chạy được; tắt ở môi trường thật.
- [ ] Không thu tiền trùng cho cùng order_id (TC-04).
- [ ] Database riêng cho payment-service.
- [ ] README ghi cách chạy (cổng 8005, biến `PAYMENT_SANDBOX`, không expose qua gateway).
- [ ] Đã `git commit` + `git tag payment-service-ok` kèm ghi chú "đã pass TC + U".

> Xong payment, bạn đã đủ điều kiện quay lại chạy **Giai đoạn B của order-service** (TC-08,
> TC-09) — vì giờ đã có cách tạo cả thanh toán thành công lẫn thất bại. Service cuối còn lại
> là shipping-service.
