# Knowledge Base — dữ liệu thật của ai-service

> Đây là **bằng chứng dữ liệu** cho Chương 3: ~750 sự kiện hành vi đi qua API thật và đồ thị
> tri thức Neo4j dựng từ chúng. Snapshot xuất ngày seed; tạo lại bất cứ lúc nào bằng
> `docker exec -e ADMIN_TOKEN=<token> ecom-ai-service python export_kb.py`.

## "750 data" nằm ở đâu?

Dữ liệu hành vi gốc sống trong **behavior store = SQLite** tại
`ai-service/ai_data/behavior.db` (bên trong container: `/app/ai_data/behavior.db`).
File đó là binary + bị `.gitignore` (dữ liệu runtime) nên không thấy trực tiếp trong repo —
vì vậy ta **export ra CSV** trong thư mục này để xem được.

## Các file

| File | Nội dung | Số dòng |
|------|----------|---------|
| `behavior_events.csv` | Toàn bộ sự kiện: `id, user_id, product_id, action, ts` | **756** |
| `behavior_summary.txt` | Tổng hợp: 50 user, view 467 / click 202 / add_to_cart 87 | — |
| `graph_edges_view_buy.csv` | Cạnh `User-[VIEW/BUY{count}]->Product` (từ events) | 582 |
| `graph_similar.csv` | Cạnh `Product-[SIMILAR{weight}]-Product` (đồng xuất hiện) | 241 |
| `accounts_seed.csv` | 50 tài khoản seed: `id, email, full_name, phone, role` | 50 |

## Cách dữ liệu được tạo (pipeline thật, không nhồi tay)

```
seed_behavior.py → POST /events (API thật, JWT)
   → ghi vào behavior store (SQLite)        [behavior_events.csv]
   → admin: POST /admin/build-graph
       → MERGE cạnh VIEW/BUY vào Neo4j       [graph_edges_view_buy.csv]
       → Cypher tính SIMILAR (đồng xuất hiện) [graph_similar.csv]
```

3 persona ↔ 3 cụm sản phẩm:
- `user00–17@seed.local` — Game thủ → cụm **điện tử**
- `user18–35@seed.local` — Sinh viên → cụm **sách**
- `user36–49@seed.local` — Thời trang → cụm **thời trang**

Mật khẩu chung: `Pass123!`.

## Xem đồ thị trực quan (demo)

Neo4j Browser `http://localhost:7474` (user `neo4j` / `ecom123`):
```cypher
MATCH (p1:Product)-[s:SIMILAR]-(p2:Product) RETURN p1, s, p2;
```
→ thấy 3 cụm sản phẩm nối nhau bằng SIMILAR.
