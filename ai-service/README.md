# ai-service

Microservice gợi ý sản phẩm + chatbot tư vấn (FastAPI, cổng **8007**). Theo plan Chương 3.

## Kiến trúc theo giai đoạn

| GĐ | Nội dung | Trạng thái |
|----|----------|-----------|
| 0  | FastAPI + `/events` + behavior store (SQLite) | ✅ |
| 1  | `/recommend` baseline phổ biến + cold start | ✅ |
| 3  | Knowledge Graph Neo4j (VIEW/BUY/SIMILAR) | ✅ |
| 4  | Chatbot retrieval trên catalog (không LLM) | ✅ |
| 2/5| Hybrid: `final = W_GRAPH·graph + W_LSTM·cooccurrence + W_POP·popularity` | ✅ (heuristic) |

> LSTM ở đây là **item-based co-occurrence** từ behavior store (stand-in nhẹ, chạy được cả khi
> Neo4j chết) — không train deep model. RAG/vector store chưa wiring (chatbot dùng keyword retrieval).

## API

| Method | Path | Auth | Mô tả |
|--------|------|------|-------|
| POST | `/events` | token | Ghi hành vi `{product_id, action}` (view/click/add_to_cart) |
| GET  | `/recommend?n=5` | token | Top-N gợi ý (hybrid + cold-start fallback) |
| POST | `/chatbot` | token | `{message}` → `{reply, suggested:[id]}` (sản phẩm có thật) |
| POST | `/admin/build-graph?threshold=5` | admin/staff | Dựng cạnh Neo4j từ behavior store + tính SIMILAR |
| GET  | `/health` | — | Health + thống kê graph |

## Chạy & seed

```bash
docker compose up -d ai-service neo4j
# Seed 50 tài khoản (form register mới) + ~750 events qua API thật:
docker exec ecom-ai-service python seed_behavior.py
# Dựng knowledge graph từ behavior store:
TOKEN=<admin access>; curl -X POST "http://localhost:8007/admin/build-graph?threshold=5" -H "Authorization: Bearer $TOKEN"
```

## Business rules đã pass (TC-01→TC-14)
- BR-1 cold start luôn có gợi ý; BR-2 chỉ gợi ý sản phẩm có thật (kiểm qua product-service)
- BR-3 không trùng, đúng N; BR-4 Neo4j/LLM chết vẫn chạy (hạ cấp); BR-5 xác định trên snapshot
- BR-6 < 0.5s; BR-7 chatbot không bịa; BR-8 cá nhân hoá theo user_id từ JWT

## Lưu ý
- Verify JWT HS256 thủ công (chung `SECRET_KEY` với user-service), không cần PyJWT.
- Behavior store = SQLite `ai_data/behavior.db` (gitignored, runtime data).
- Neo4j cần mật khẩu ≥ 8 ký tự HOẶC override `NEO4J_dbms_security_auth__minimum__password__length` (đã set ở compose).
