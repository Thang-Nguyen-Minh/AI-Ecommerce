# ai-service

Microservice gợi ý sản phẩm + chatbot tư vấn (FastAPI, cổng **8007**). Theo plan Chương 3.

## Kiến trúc theo giai đoạn

| GĐ | Nội dung | Trạng thái |
|----|----------|-----------|
| 0  | FastAPI + `/events` + behavior store (SQLite) | ✅ |
| 1  | `/recommend` baseline phổ biến + cold start | ✅ |
| 3  | Knowledge Graph Neo4j (VIEW/BUY/SIMILAR) | ✅ |
| 4  | Chatbot RAG: vector store ngữ nghĩa (FAISS + sentence-transformers) + reply Auto (LLM/mẫu) | ✅ |
| 2/5| Hybrid: `final = W_GRAPH·graph + W_LSTM·lstm + W_POP·popularity` | ✅ |

> **LSTM thật**: model torch Embedding→LSTM→Linear train next-item từ behavior store
> (`train_lstm.py`, snapshot đóng băng `ai_data/lstm/model.pt`, eval → xác định). Không có
> snapshot → tự hạ cấp về item-based co-occurrence (BR-4).
> **RAG thật**: embed mô tả sản phẩm (sentence-transformers, model cache sẵn) → FAISS index
> (`ai_data/vector/`). Chatbot tìm kiếm ngữ nghĩa → reply Auto: có `OPENAI_API_KEY` thì GPT
> (grounding chống bịa), không có thì mẫu. Vector chết → fallback keyword → popularity.

## API

| Method | Path | Auth | Mô tả |
|--------|------|------|-------|
| POST | `/events` | token | Ghi hành vi `{product_id, action}` (view/click/add_to_cart) |
| GET  | `/recommend?n=5` | token | Top-N gợi ý (hybrid + cold-start fallback) |
| POST | `/chatbot` | token | `{message}` → `{reply, suggested:[id]}` (sản phẩm có thật) |
| POST | `/admin/build-graph?threshold=5` | admin/staff | Dựng cạnh Neo4j từ behavior store + tính SIMILAR |
| POST | `/admin/build-vector` | admin/staff | Dựng FAISS index từ catalog (RAG) |
| GET  | `/health` | — | Health + thống kê graph + vector |

## Chạy & seed

```bash
docker compose up -d ai-service neo4j
# Seed 50 tài khoản (form register mới) + ~750 events qua API thật:
docker exec ecom-ai-service python seed_behavior.py
# Dựng knowledge graph từ behavior store:
TOKEN=<admin access>; curl -X POST "http://localhost:8007/admin/build-graph?threshold=5" -H "Authorization: Bearer $TOKEN"
# Dựng vector index cho RAG chatbot:
curl -X POST "http://localhost:8007/admin/build-vector" -H "Authorization: Bearer $TOKEN"
# Train LSTM next-item (snapshot ai_data/lstm/model.pt):
docker exec ecom-ai-service python train_lstm.py
```

## Business rules đã pass (TC-01→TC-14)
- BR-1 cold start luôn có gợi ý; BR-2 chỉ gợi ý sản phẩm có thật (kiểm qua product-service)
- BR-3 không trùng, đúng N; BR-4 Neo4j/LLM chết vẫn chạy (hạ cấp); BR-5 xác định trên snapshot
- BR-6 < 0.5s; BR-7 chatbot không bịa; BR-8 cá nhân hoá theo user_id từ JWT

## Lưu ý
- Verify JWT HS256 thủ công (chung `SECRET_KEY` với user-service), không cần PyJWT.
- Behavior store = SQLite `ai_data/behavior.db` (gitignored, runtime data).
- Neo4j cần mật khẩu ≥ 8 ký tự HOẶC override `NEO4J_dbms_security_auth__minimum__password__length` (đã set ở compose).
