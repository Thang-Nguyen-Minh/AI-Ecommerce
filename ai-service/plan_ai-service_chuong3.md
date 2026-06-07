# Plan Chương 3 — ai-service (tư vấn & gợi ý sản phẩm)

> Cùng khung với các contract trước, nhưng có thêm hai mục riêng cho đặc thù AI: **kế
> hoạch dựng theo giai đoạn** (mục 5) và **cách kiểm thử AI** (mục 6). ai-service chạy
> FastAPI ở **cổng 8007** (tech stack mục 3.9: PyTorch/TensorFlow + Neo4j + FAISS + FastAPI).
>
> Khác biệt cốt lõi cần nhớ: đây là service học máy, output **không cố định**. Đừng cố
> assert "gợi ý phải đúng [101,102,205]". Thay vào đó kiểm cái có thể kiểm chắc chắn: hình
> dạng response, tính hợp lệ của kết quả, hành vi khi thiếu dữ liệu, khi thành phần con chết,
> độ trễ — và đo chất lượng riêng bằng chỉ số.

---

## 1. Phạm vi (Bounded Context)

ai-service là microservice độc lập (tài liệu 3.2) làm hai việc (tài liệu 3.8):

1. **Danh sách gợi ý** (recommendation): trả top-N sản phẩm cho một user, dùng khi xem hàng / thêm giỏ.
2. **Chatbot tư vấn**: nhận câu hỏi tự nhiên, trả lời kèm sản phẩm phù hợp.

Đầu vào: hành vi người dùng (view/click/add_to_cart) và truy vấn. Xử lý: LSTM + Knowledge
Graph + RAG, kết hợp thành điểm hybrid (3.4–3.7). Không đụng DB service khác; đọc dữ liệu
sản phẩm qua product-service khi cần xác minh.

---

## 2. Thành phần & dữ liệu

| Thành phần        | Vai trò (tài liệu)                       | Lưu ở đâu                  |
|-------------------|------------------------------------------|----------------------------|
| Behavior store    | Log hành vi user (3.3)                    | DB riêng của ai-service    |
| LSTM model        | Dự đoán sản phẩm tiếp theo từ chuỗi (3.4) | file model (snapshot)      |
| Knowledge Graph   | Quan hệ User/Product: BUY/VIEW/SIMILAR (3.5) | Neo4j                   |
| Vector DB         | Embedding mô tả sản phẩm cho RAG (3.6)    | FAISS/Chroma               |
| Hybrid scorer     | `final = w1·lstm + w2·graph + w3·rag` (3.7)| trong service             |

**BehaviorEvent** (bám sát 3.3.1)

| Field      | Kiểu     | Ràng buộc                                   |
|------------|----------|---------------------------------------------|
| id         | int      | PK                                          |
| user_id    | int      | bắt buộc                                    |
| product_id | int      | bắt buộc                                    |
| action     | string   | trong {view, click, add_to_cart}            |
| timestamp  | datetime | bắt buộc                                    |

---

## 3. Luật nghiệp vụ (Business Rules)

- **BR-1 (cold start)**: User chưa có lịch sử → vẫn trả gợi ý (fallback sang sản phẩm phổ
  biến/bán chạy), **không** trả rỗng, **không** lỗi 500. Đây là luật quan trọng nhất của AI service.
- **BR-2 (gợi ý hợp lệ)**: Mọi `product_id` trả ra phải là sản phẩm **đang tồn tại** (xác
  minh qua product-service). Không gợi ý sản phẩm đã xóa.
- **BR-3 (đúng định dạng)**: Danh sách gợi ý không trùng lặp, đúng số lượng `n` yêu cầu (top-N).
- **BR-4 (chịu lỗi từng phần)**: Nếu một thành phần con (Neo4j / Vector DB / LLM) không phản
  hồi, service hạ cấp xuống các tín hiệu còn lại hoặc baseline — **không** sập cả endpoint.
- **BR-5 (xác định để test được)**: Với model đã đóng băng (snapshot) và seed cố định, cùng
  input → cùng output. Test tự động chỉ chạy trên model đóng băng, không chạy trên model đang
  học online (tránh test chập chờn).
- **BR-6 (độ trễ)**: `/recommend` phải trả trong ngân sách thời gian (vd < 500ms) vì nó nằm
  trong luồng duyệt hàng/thêm giỏ.
- **BR-7 (chatbot không bịa)**: Chatbot chỉ giới thiệu sản phẩm **có thật** lấy từ bước
  retrieve. Không tự nghĩ ra tên/giá sản phẩm không tồn tại.
- **BR-8 (riêng tư & phạm vi)**: Hành vi gắn với `user_id`; gợi ý cá nhân hóa theo đúng user.

---

## 4. API (bám sát tài liệu 3.8)

Base URL local: `http://localhost:8007`.

| Method | Đường dẫn   | Quyền cần | Body / Query                       | Trả ra (thành công)                              |
|--------|-------------|-----------|-------------------------------------|--------------------------------------------------|
| POST   | /events     | token     | `{product_id, action}`              | 201 (ghi nhận hành vi; user_id lấy từ token)     |
| GET    | /recommend  | token     | `?n=5` (user_id lấy từ token)       | 200 + `{items:[{product_id, score?}, ...]}`      |
| POST   | /chatbot    | token     | `{message}`                         | 200 + `{reply, suggested:[product_id, ...]}`     |

> Hợp đồng: `/recommend` luôn trả mảng `items` (có thể rỗng-fallback nhưng theo BR-1 phải có
> phần tử). `/chatbot` luôn trả `reply` (chuỗi) + `suggested` (mảng product_id có thật).

---

## 5. Kế hoạch dựng theo giai đoạn (build plan)

Nguyên tắc: **dựng baseline chạy được trước, ghép ML sau.** Như vậy API + cold start + tích
hợp UI hoạt động đầu-cuối ngay từ sớm, các mô hình ML chỉ là nâng cấp chất lượng — không bị
kẹt chờ model xong mới có endpoint. Mỗi giai đoạn có "cổng test" phải xanh mới sang giai đoạn sau.

| GĐ | Mục tiêu | Cổng test phải pass |
|----|----------|---------------------|
| 0  | Khung FastAPI + thu thập hành vi (`/events`, behavior store) | TC-01 → TC-03 |
| 1  | **Baseline gợi ý theo độ phổ biến** (chưa cần ML) — chốt hợp đồng API + cold start | TC-04 → TC-06 |
| 2  | LSTM (chuỗi hành vi) thay/bổ sung baseline (3.4) | TC-07; sanity TC-14 |
| 3  | Knowledge Graph trên Neo4j (3.5) | TC-09 (hạ cấp) |
| 4  | RAG + Vector DB + chatbot (3.6, 3.8.2) | TC-11 → TC-13 |
| 5  | Kết hợp Hybrid + chỉnh trọng số (3.7) | TC-08, TC-10 |

> Mẹo giao việc cho AI: yêu cầu làm **đúng từng giai đoạn**, không nhảy thẳng tới hybrid.
> "Dựng giai đoạn 1: /recommend trả top-N theo sản phẩm phổ biến, kèm fallback cold start.
> Đưa tôi lệnh curl test." Khi cổng test GĐ1 xanh mới sang GĐ2.

---

## 6. Cách kiểm thử AI (đọc trước khi làm mục 7)

Tách rõ hai loại — đây là chỗ nhiều người làm sai và bị test chập chờn:

**(A) Test hợp đồng — assert cứng, cho vào kiểm thử tự động.** Kiểm những thứ luôn đúng bất
kể model: response có đúng cấu trúc không, đủ `n` phần tử không, có trùng không, product_id
có tồn tại không, cold start có trả fallback không, thành phần con chết có sập không, độ trễ
có trong ngân sách không. Đây là phần "nghiệp vụ chuẩn" của AI service.

**(B) Đánh giá chất lượng — đo bằng chỉ số, làm định kỳ, KHÔNG nhét vào test tự động.** Gợi ý
có "đúng/hay" không là chuyện xác suất. Đánh giá bằng tập mẫu nhỏ có gán nhãn và chỉ số như
precision@k / hit-rate, hoặc kiểm bằng mắt vài ca tiêu biểu. Đặt ngưỡng (vd "precision@5 ≥
0.3"), không assert bằng nhau tuyệt đối.

Quy tắc vàng: nếu một phép kiểm có thể cho kết quả khác nhau giữa hai lần chạy mà cả hai đều
hợp lý → nó thuộc loại (B), không phải (A).

---

## 7. Kiểm thử back-end (test case)

Token lấy từ user-service. Gọi tới cổng 8007.

### Nhóm thu thập hành vi (GĐ0)

#### TC-01 — Ghi nhận hành vi hợp lệ
```bash
curl -i -X POST http://localhost:8007/events \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":101,"action":"view"}'
```
Mong đợi: `201`, sự kiện được lưu với user_id lấy từ token.

#### TC-02 — Action không hợp lệ bị chặn (BR)
```bash
curl -i -X POST http://localhost:8007/events \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":101,"action":"haha"}'
```
Mong đợi: `400`. Chỉ nhận view/click/add_to_cart.

#### TC-03 — Không token thì không ghi được (BR-8)
```bash
curl -i -X POST http://localhost:8007/events \
  -H "Content-Type: application/json" -d '{"product_id":101,"action":"view"}'
```
Mong đợi: `401`.

### Nhóm hợp đồng gợi ý (GĐ1+)

#### TC-04 — Trả đúng số lượng, không trùng (BR-3)
```bash
curl -i "http://localhost:8007/recommend?n=5" \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>"
```
Mong đợi: `200`, `items` có **đúng 5** phần tử (hoặc ít hơn nếu catalog nhỏ), không có
product_id trùng nhau.

#### TC-05 — Cold start vẫn có gợi ý (BR-1) ⚠️ luật cốt lõi AI
Dùng token của một user **chưa có hành vi nào** (vd khach2 mới tạo):
```bash
curl -i "http://localhost:8007/recommend?n=5" \
  -H "Authorization: Bearer <ACCESS_CUSTOMER_2>"
```
Mong đợi: `200`, `items` **không rỗng** (fallback sản phẩm phổ biến), không `500`.

#### TC-06 — Mọi gợi ý đều là sản phẩm có thật (BR-2) ⚠️ liên service
Lấy từng `product_id` trong kết quả TC-04, kiểm qua product-service:
```bash
curl -i http://localhost:8002/products/<product_id>
```
Mong đợi: mỗi id trả `200` (tồn tại). Không có id nào trả `404`.

#### TC-07 — Xác định trên model đóng băng (BR-5)
Với model snapshot + seed cố định, gọi `/recommend?n=5` hai lần cho cùng user.
Mong đợi: hai danh sách **giống hệt** nhau. (Nếu khác → model đang học online lẫn vào test;
tách ra dùng snapshot.)

#### TC-08 — Độ trễ trong ngân sách (BR-6)
```bash
curl -o /dev/null -s -w "Thoi gian: %{time_total}s\n" \
  "http://localhost:8007/recommend?n=5" \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>"
```
Mong đợi: thời gian dưới ngân sách đặt ra (vd < 0.5s).

### Nhóm chịu lỗi từng phần (GĐ3+)

#### TC-09 — Neo4j chết, gợi ý vẫn chạy (BR-4) ⚠️ chịu lỗi
Tắt Neo4j, gọi lại `/recommend`.
Mong đợi: `200`, vẫn trả `items` (hạ cấp sang LSTM/baseline), **không** `500`. Log có cảnh
báo thành phần graph không khả dụng.

#### TC-10 — LLM/Vector DB chết, chatbot hạ cấp (BR-4)
Tắt LLM/vector DB, gọi `/chatbot`.
Mong đợi: trả thông báo thân thiện (vd "hệ thống tư vấn tạm bận, đây là vài sản phẩm phổ
biến") kèm `suggested` từ baseline; `/recommend` không bị ảnh hưởng.

### Nhóm chatbot (GĐ4)

#### TC-11 — Chatbot trả lời kèm sản phẩm có thật (BR-7) ⚠️ chống bịa
```bash
curl -i -X POST http://localhost:8007/chatbot \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" \
  -d '{"message":"tôi cần laptop giá rẻ"}'
```
Mong đợi: `200`, có `reply` (chuỗi) và `suggested` (mảng product_id). Mỗi id trong
`suggested` kiểm qua product-service đều tồn tại.

#### TC-12 — Câu hỏi rỗng/vô nghĩa không làm sập (BR)
```bash
curl -i -X POST http://localhost:8007/chatbot \
  -H "Authorization: Bearer <ACCESS_CUSTOMER>" \
  -H "Content-Type: application/json" -d '{"message":"asdfgh"}'
```
Mong đợi: `200` với câu trả lời hạ cấp lịch sự, không `500`, không treo.

#### TC-13 — Chatbot không giới thiệu hàng không tồn tại (BR-7)
Quét toàn bộ `suggested` của vài câu hỏi, đối chiếu product-service.
Mong đợi: không có product_id nào không tồn tại. (Đây là phòng "ảo giác" của LLM.)

### Nhóm chất lượng — loại (B), đánh giá riêng, không assert cứng

#### TC-14 — Sanity: gợi ý bám theo sở thích
Tạo lịch sử cho một user toàn hành vi với sản phẩm nhóm "laptop", rồi xem `/recommend`.
Đánh giá: phần lớn gợi ý nên thuộc nhóm điện tử/laptop. Đo bằng tỉ lệ trùng nhóm hoặc kiểm
bằng mắt; đặt ngưỡng thay vì so bằng. Nếu lệch hẳn (toàn gợi ý quần áo) → xem lại pipeline.

---

## 8. Kiểm thử giao diện (UI)

> Làm sau khi mục 7 (phần hợp đồng) xanh. Mỗi mục gắn một luật nghiệp vụ.

- [ ] **U-01**: Trang sản phẩm / sau khi thêm giỏ → hiện khối "Gợi ý cho bạn" với vài sản phẩm.
- [ ] **U-02 (BR-2)**: Bấm vào một sản phẩm được gợi ý → mở đúng trang sản phẩm đó, không
  gặp link gãy/404.
- [ ] **U-03 (BR-1)**: User mới (chưa có lịch sử) vẫn thấy khối gợi ý (hàng phổ biến), không
  để trống/vỡ layout.
- [ ] **U-04 (BR-7)**: Mở chatbot, hỏi một câu → nhận câu trả lời kèm sản phẩm bấm được; bấm
  gợi ý mở đúng sản phẩm thật.
- [ ] **U-05 (BR-6)**: Trong lúc chờ chatbot/gợi ý, có trạng thái "đang tải"; không xoay vô
  hạn; quá thời gian thì báo lỗi nhẹ nhàng.
- [ ] **U-06 (BR-4)**: Khi ai-service chết → khối gợi ý ẩn đi hoặc hiện "sản phẩm phổ biến",
  trang chính **không** vỡ; chatbot báo tạm bận.
- [ ] **U-07**: Gõ câu rỗng/vô nghĩa vào chatbot → UI xử lý gọn, không hiện lỗi kỹ thuật thô.

---

## 9. Definition of Done

- [ ] Mỗi giai đoạn (mục 5) đều qua cổng test của nó trước khi sang giai đoạn sau.
- [ ] Test hợp đồng back-end: TC-01 → TC-13 pass.
- [ ] Có đánh giá chất lượng (loại B) với chỉ số + ngưỡng (vd precision@5), ghi lại kết quả; TC-14 sanity đạt.
- [ ] UI: U-01 → U-07 pass.
- [ ] Cold start luôn trả gợi ý (TC-05); gợi ý luôn là sản phẩm có thật (TC-06, TC-13).
- [ ] Hạ cấp được khi Neo4j/LLM/Vector DB chết (TC-09, TC-10) — không sập endpoint.
- [ ] ai-service độc lập, giao tiếp các service khác qua API (tài liệu 3.9).
- [ ] README ghi cách chạy (cổng 8007, kết nối Neo4j/Vector DB, đường dẫn model snapshot).
- [ ] Đã `git commit` + `git tag ai-service-ok` kèm ghi chú test + chỉ số chất lượng.

> Khi ai-service xanh, ghép nó vào kiểm thử đầu-cuối: sau bước "thêm giỏ" và "xem sản phẩm",
> khối gợi ý và chatbot phải hoạt động — khớp với luồng tài liệu 3.1.
