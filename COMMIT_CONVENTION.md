# Commit Convention — ecom-final

Quy tắc commit cho dự án microservices này. Mọi commit (kể cả commit do AI tạo) phải theo format và thứ tự dưới đây.

---

## Format commit message

```
<type>(<scope>): <mô tả ngắn>

<body — tuỳ chọn, giải thích WHY nếu cần>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>  ← nếu AI viết code
```

### Các `type` được dùng

| Type     | Dùng khi nào |
|----------|-------------|
| `feat`   | Thêm tính năng mới (endpoint, UI, model) |
| `fix`    | Sửa bug nghiệp vụ hoặc logic sai |
| `chore`  | Config, setup, tooling, dependencies — không ảnh hưởng logic |
| `docs`   | Chỉ sửa tài liệu (README, contract, comment) |
| `style`  | Sửa format, CSS, UI thuần mỹ quan — không đổi logic |
| `refactor` | Tái cấu trúc code, không thêm tính năng / sửa bug |
| `test`   | Thêm hoặc sửa test |
| `revert` | Hoàn tác commit trước |

### Các `scope` theo service

| Scope            | Dùng cho |
|------------------|---------|
| `user-service`   | Backend user-service |
| `product-service`| Backend product-service |
| `cart-service`   | Backend cart-service |
| `order-service`  | Backend order-service |
| `payment-service`| Backend payment-service |
| `shipping-service`| Backend shipping-service |
| `ai-service`     | Backend AI service |
| `frontend`       | Tất cả HTML/JS/CSS |
| `infra`          | docker-compose, nginx, entrypoint |
| `db`             | Migration, SQL init script |

---

## Thứ tự commit khi hoàn thành một service

Mỗi lần làm xong một service, commit theo đúng thứ tự này:

```
1. fix(user-service): ...        ← sửa bug trước nếu có
2. feat(user-service): ...       ← backend hoàn chỉnh
3. feat(frontend): ...           ← UI của service đó
4. chore(infra): ...             ← cập nhật docker-compose / nginx nếu có thay đổi
5. docs: ...                     ← README, contract
```

> **Quy tắc**: Backend trước → Frontend sau → Infra nếu cần → Docs cuối.
> Không bao giờ commit docs trước khi code chạy được.

---

## Thứ tự commit theo tiến độ dự án

Làm xong service nào thì commit service đó, theo thứ tự phụ thuộc:

```
1. chore(infra)         ← docker-compose, gateway (làm 1 lần đầu)
2. feat(user-service)   ← auth, user, JWT — service nền tảng
3. feat(product-service)← catalog, search — không phụ thuộc user
4. feat(cart-service)   ← cần user + product
5. feat(order-service)  ← cần cart + product
6. feat(payment-service)← cần order
7. feat(shipping-service)← cần order + payment
8. feat(ai-service)     ← cần product (knowledge graph, recommendation)
9. feat(frontend)       ← commit theo từng luồng (login, shop, checkout, ...)
```

---

## Quy tắc bổ sung

- **1 commit = 1 mục đích rõ ràng** — không nhét "sửa nhiều thứ linh tinh" vào 1 commit
- **Không commit `.env`** — chỉ commit `.env.example`
- **Commit migrations cùng model** — khi thêm/sửa model Django, commit migration luôn trong cùng commit
- **Tag sau khi service pass hết test** — ví dụ: `git tag user-service-ok`
- **Mô tả ngắn ≤ 72 ký tự**, viết thường, không dấu chấm cuối
- **Body (nếu có)** giải thích *tại sao* thay đổi, không giải thích *cái gì* (code tự nói được điều đó)

---

## Ví dụ thực tế

```bash
# Đúng
feat(user-service): add address CRUD endpoints
fix(user-service): force role=customer on public register (BR-1)
chore(infra): add nginx routing for cart-service
docs: update user-service README with BR table

# Sai
git commit -m "update code"
git commit -m "fix bug"
git commit -m "WIP"
git commit -m "sửa lỗi đăng nhập và thêm sản phẩm mới và update README"
```
