# Plan: Seed Knowledge Base (Neo4j Graph cho ai-service)

> Mục tiêu: tạo đồ thị tri thức Neo4j **qua đường pipeline thật** (không nhồi Cypher tay),
> để gợi ý có nghĩa và demo không vỡ khi thầy click trực tiếp. Bám sát mô hình đồ thị tài
> liệu mục 3.5 (Node User/Product; Edge BUY/VIEW/SIMILAR) và truy vấn gợi ý 3.5.3.
>
> Nguyên tắc cốt lõi: **dữ liệu phải có mẫu (persona), không random.** Cạnh SIMILAR chỉ có
> nghĩa khi hành vi tương quan theo cụm. Random → SIMILAR là nhiễu → gợi ý ngớ ngẩn.

---

## 1. Sản phẩm đầu ra

Sau khi chạy plan này, bạn có:
- ~50 tài khoản thật trong user-service.
- ~750 sự kiện hành vi đi qua `POST /events` thật → tạo cạnh VIEW/BUY trong Neo4j.
- Các cạnh SIMILAR có trọng số, tạo thành cụm sản phẩm rõ ràng.
- `/recommend` trả gợi ý "đúng gu" theo cụm, và một click mới lúc demo vẫn cập nhật được.

---

## 2. Phụ thuộc & thứ tự chạy

Chạy theo đúng thứ tự (mỗi bước dựa vào bước trước):

1. **product-service (:8002)** đang chạy, đã seed catalog ở mục 3 → có `product_id` thật.
   (Bắt buộc, vì gợi ý phải trỏ tới sản phẩm có thật — ai-service BR-2.)
2. **user-service (:8000)** đang chạy → tạo được 50 tài khoản + cấp token.
3. **ai-service (:8007) + Neo4j** đang chạy → `POST /events` ghi cạnh vào graph.
4. Chạy **script sinh hành vi** (mục 6).
5. Chạy **Cypher tính SIMILAR** (mục 7).
6. Kiểm bằng **truy vấn gợi ý** (mục 8) rồi **demo** (mục 9).

---

## 3. Catalog sản phẩm theo cụm

Tạo các sản phẩm này trong product-service (token admin, theo contract product-service).
Dùng đúng `product_id` mà product-service trả về — bảng dưới chỉ là id ví dụ để map persona.

| Cụm        | Sản phẩm ví dụ                                              | id ví dụ           |
|------------|-------------------------------------------------------------|--------------------|
| Gaming     | Laptop gaming, Chuột gaming, Bàn phím cơ, Tai nghe gaming, Ghế gaming | 101–105   |
| Học/VP     | Laptop văn phòng, Giáo trình Python, Balo laptop, Chuột không dây, SSD | 201–205  |
| Thời trang | Áo thun, Quần jeans, Giày sneaker, Mũ lưỡi trai, Thắt lưng   | 301–305            |
| Phổ biến (chéo cụm) | Tai nghe Bluetooth, Sạc dự phòng                  | 401–402            |

> Hai món "phổ biến" được nhiều persona chạm tới → tạo chút cạnh liên cụm cho thực tế, và
> làm nguồn fallback cold start (mục 8).

---

## 4. Personas & phân bổ

Gán mỗi tài khoản một persona, mỗi persona bám một cụm. Tổng 50 tài khoản:

| Persona     | Cụm chính | Số tài khoản |
|-------------|-----------|--------------|
| Game thủ    | Gaming    | 18           |
| Sinh viên   | Học/VP    | 18           |
| Thời trang  | Thời trang| 14           |

Mỗi tài khoản sinh ~12–18 sự kiện: phần lớn trong cụm của mình, lác đác chạm món phổ biến,
và ~5% "nhiễu" sang cụm khác cho giống thật (không để các cụm tách rời tuyệt đối).

---

## 5. Quy ước event → cạnh đồ thị

ai-service ánh xạ sự kiện thành cạnh (cài trong logic service, không nhồi tay):

| Event (`action`)        | Cạnh tạo trong Neo4j                         |
|-------------------------|----------------------------------------------|
| `view`, `click`         | `(User)-[:VIEW {count}]->(Product)` (cộng dồn)|
| `add_to_cart`           | `(User)-[:BUY {count}]->(Product)` (coi là ý định mua) |

> Nếu muốn cạnh BUY "thật" hơn, cho một phần add_to_cart đi tiếp qua luồng order → payment
> thành công (các service đã dựng). Không bắt buộc cho demo; coi add_to_cart = BUY là đủ.

---

## 6. Script sinh hành vi (spec để AI cài + chạy)

Logic: với mỗi tài khoản → đăng nhập lấy token → gửi N sự kiện theo persona qua `POST /events`.
Vì đi qua API thật, pipeline tự tạo cạnh VIEW/BUY. Bản phác Python:

```python
import requests, random

BASE_USER = "http://localhost:8000"
BASE_AI   = "http://localhost:8007"
PASSWORD  = "Pass123!"

CLUSTERS = {
    "gaming":  [101, 102, 103, 104, 105],
    "study":   [201, 202, 203, 204, 205],
    "fashion": [301, 302, 303, 304, 305],
}
POPULAR  = [401, 402]
ALL      = sum(CLUSTERS.values(), []) + POPULAR
PERSONAS = ["gaming"]*18 + ["study"]*18 + ["fashion"]*14   # = 50

def ensure_account(username):
    # đăng ký (role mặc định customer) — bỏ qua nếu đã tồn tại
    requests.post(f"{BASE_USER}/auth/register",
                  json={"username": username, "password": PASSWORD})
    r = requests.post(f"{BASE_USER}/auth/login",
                      json={"username": username, "password": PASSWORD})
    return r.json()["access"]

for i, persona in enumerate(PERSONAS):
    username = f"user{i:02d}"
    token = ensure_account(username)
    headers = {"Authorization": f"Bearer {token}"}
    items = CLUSTERS[persona]
    for _ in range(random.randint(12, 18)):
        r = random.random()
        if   r < 0.80: pid = random.choice(items)        # trong cụm
        elif r < 0.95: pid = random.choice(POPULAR)       # món phổ biến
        else:          pid = random.choice(ALL)           # nhiễu
        action = random.choices(["view", "click", "add_to_cart"],
                                weights=[6, 3, 1])[0]
        requests.post(f"{BASE_AI}/events", headers=headers,
                      json={"product_id": pid, "action": action})

print("Seed xong.")
```

> Mẹo giao AI: "Cài script seed theo spec này, dùng đúng product_id thật từ product-service,
> chạy và in số event đã gửi." Không cho nó tự chế random toàn bộ — giữ cấu trúc persona.

---

## 7. Tính cạnh SIMILAR (Cypher — chạy sau khi seed)

SIMILAR = hai sản phẩm hay được **cùng một người** tương tác (đồng xuất hiện). Đây là phần
làm gợi ý có chiều sâu:

```cypher
MATCH (u:User)-[:VIEW|BUY]->(p1:Product)
MATCH (u)-[:VIEW|BUY]->(p2:Product)
WHERE id(p1) < id(p2)
WITH p1, p2, count(DISTINCT u) AS co
WHERE co >= 5
MERGE (p1)-[s:SIMILAR]-(p2)
SET s.weight = co;
```

> Ngưỡng `co >= 5` là điểm khởi đầu (mỗi cụm ~14–18 user). Nếu SIMILAR quá thưa → hạ xuống
> 3–4. Quá dày, nối cả các cụm khác nhau → nâng lên. Chỉnh tới khi cụm rõ trong Neo4j Browser.

Kiểm nhanh đồ thị (chạy trong Neo4j Browser để thấy cụm — rất hợp để demo):

```cypher
MATCH (p1:Product)-[s:SIMILAR]-(p2:Product)
RETURN p1, s, p2;
```

---

## 8. Truy vấn gợi ý (Cypher)

**Gợi ý cá nhân hóa** (bám sát tài liệu 3.5.3): từ sản phẩm user đã tương tác, nhảy sang
sản phẩm SIMILAR mà họ **chưa** chạm, xếp theo tổng trọng số:

```cypher
MATCH (u:User {id: $userId})-[:VIEW|BUY]->(p:Product)-[s:SIMILAR]-(rec:Product)
WHERE NOT (u)-[:VIEW|BUY]->(rec)
RETURN rec.id AS product_id, sum(s.weight) AS score
ORDER BY score DESC
LIMIT $n;
```

**Fallback cold start** (user chưa có hành vi — ai-service BR-1): trả sản phẩm phổ biến nhất:

```cypher
MATCH (:User)-[r:VIEW|BUY]->(p:Product)
RETURN p.id AS product_id, count(r) AS pop
ORDER BY pop DESC
LIMIT $n;
```

> `/recommend` của ai-service gọi truy vấn cá nhân hóa trước; nếu rỗng (user mới) thì rơi
> sang fallback. Đây chính là TC-05 trong plan Chương 3.

---

## 9. Kịch bản demo (hai nhịp)

**Nhịp 1 — cho thấy KB có thật và có cấu trúc:**
1. Mở Neo4j Browser, chạy truy vấn ở mục 7 → thầy thấy ba cụm sản phẩm nối nhau bằng SIMILAR
   (hình ảnh đồ thị rất trực quan).
2. Đăng nhập một tài khoản game thủ đã seed → gọi `/recommend` → gợi ý ra toàn đồ gaming
   chưa chạm (trông "đúng gu").

**Nhịp 2 — chứng minh pipeline còn sống (chốt hạ):**
3. Ngay tại chỗ, dùng một tài khoản, `POST /events` vài lần với sản phẩm cụm thời trang.
4. Chạy lại truy vấn graph / `/recommend` → cạnh mới xuất hiện, gợi ý đổi theo.
5. Nếu thầy hỏi "dữ liệu thật không?" → trả lời thẳng: dữ liệu tổng hợp nhưng chạy qua đúng
   pipeline thật. Đây là câu trả lời chuẩn và tự tin cho một đồ án.

---

## 10. Checklist nghiệm thu

- [ ] Catalog ở mục 3 đã tạo trong product-service, ghi lại `product_id` thật.
- [ ] 50 tài khoản tạo qua user-service; mỗi tài khoản đăng nhập được.
- [ ] Script seed chạy qua `POST /events` thật (KHÔNG insert Cypher tay) — kiểm: gửi một
  event test rồi xác nhận xuất hiện cạnh VIEW/BUY tương ứng trong Neo4j.
- [ ] Cạnh SIMILAR tồn tại, có `weight`, và nhìn thấy cụm rõ trong Neo4j Browser.
- [ ] Truy vấn cá nhân hóa trả gợi ý trong-cụm cho một user persona.
- [ ] Cold start trả sản phẩm phổ biến, không rỗng (BR-1).
- [ ] Mọi `product_id` gợi ý đều tồn tại ở product-service (BR-2).
- [ ] Click trực tiếp lúc demo cập nhật được graph (nhịp 2) — bằng chứng pipeline sống.

> Lưu ý phân biệt: đồ thị Neo4j này dựng từ **hành vi**. Vector store của RAG (đoạn code bạn
> đang học) dựng từ **mô tả sản phẩm** cho chatbot — kho khác, cách seed khác, ghép ở mô hình
> hybrid mục 3.7. Đừng trộn hai cái.
