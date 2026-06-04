# Chương 3 — ai-service: Tổng kết

> Microservice gợi ý + chatbot (FastAPI, cổng 8007). Dựng theo plan
> `plan_ai-service_chuong3.md` + `plan_seed_knowledge_base.md`, theo đúng thứ tự giai đoạn.

## 1. Đã làm gì (theo giai đoạn)

| GĐ | Nội dung | File chính | Cổng test |
|----|----------|-----------|-----------|
| **0** | Khung FastAPI, xác thực JWT (HS256 thủ công, chung SECRET_KEY), `POST /events`, behavior store SQLite | `app/main.py`, `app/auth.py`, `app/db.py`, `app/routers/events.py` | TC-01→03 ✅ |
| **Seed** | 50 tài khoản (form register mới) + **755 events** qua `/events` thật | `seed_behavior.py` | — |
| **1** | `/recommend` baseline phổ biến + cold-start fallback, validate sản phẩm tồn tại | `app/services/recommend_service.py` | TC-04→08 ✅ |
| **3** | Knowledge Graph Neo4j: cạnh VIEW/BUY (live + batch), SIMILAR (Cypher), gợi ý theo graph | `app/graph.py`, `app/routers/admin.py` | TC-09, TC-14 ✅ |
| **4** | Chatbot **RAG thật**: vector store ngữ nghĩa (FAISS + sentence-transformers) + reply Auto (GPT nếu có key, không thì mẫu) | `app/vector_store.py`, `app/services/chatbot_service.py` | TC-11→13 ✅ |
| **2** | **LSTM thật**: torch Embedding→LSTM→Linear next-item, snapshot đóng băng | `app/lstm_model.py`, `train_lstm.py` | TC-07, TC-14 ✅ |
| **5** | Hybrid: `final = W_GRAPH·graph + W_LSTM·lstm + W_POP·popularity` | `recommend_service.py` | TC-08, TC-10 ✅ |

## 2. API

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/events` | Ghi hành vi `{product_id, action}` (token) |
| GET  | `/recommend?n=5` | Top-N gợi ý hybrid + cold start |
| POST | `/chatbot` | `{message}` → `{reply, suggested:[id]}` (RAG, sản phẩm có thật) |
| POST | `/admin/build-graph` | Dựng cạnh Neo4j + SIMILAR (admin/staff) |
| POST | `/admin/build-vector` | Dựng FAISS index cho RAG (admin/staff) |
| GET  | `/health` | events + graph + vector stats |

## 3. Business rules đã thỏa (TC-01→TC-14)

- BR-1 cold start luôn có gợi ý; BR-2 chỉ gợi ý sản phẩm có thật; BR-3 đúng N, không trùng
- BR-4 hạ cấp khi Neo4j / vector / LLM chết — không sập (cached availability, fast-fail)
- BR-5 xác định trên snapshot (LSTM `eval()`); BR-6 `/recommend` ~0.06s < 0.5s
- BR-7 chatbot không bịa (suggested luôn từ catalog); BR-8 cá nhân hoá theo user_id từ JWT

## 4. Dữ liệu (xem `knowledge_base/`)

- **755 events** trong behavior store (SQLite `ai_data/behavior.db`) → export CSV.
- Graph Neo4j: **50 user, 58 product, 241 cặp SIMILAR** (482 cạnh 2 chiều).
- Sanity gu: gamer → 4/5 điện tử, student → 5/5 sách.

## 5. Chạy lại từ đầu

```bash
docker compose up -d ai-service neo4j
docker exec ecom-ai-service python seed_behavior.py          # 50 acc + 755 events
TOKEN=<admin>;  # login admin@ecom.local / Admin123!
curl -X POST localhost:8007/admin/build-graph?threshold=5 -H "Authorization: Bearer $TOKEN"
curl -X POST localhost:8007/admin/build-vector            -H "Authorization: Bearer $TOKEN"
docker exec ecom-ai-service python train_lstm.py             # train LSTM
docker exec -e ADMIN_TOKEN=$TOKEN ecom-ai-service python export_kb.py  # xuất CSV
```

## 6. Trung thực về phạm vi

- LSTM train trên dữ liệu nhỏ (~15 event/user, vocab 58) → model gọn cho demo có cấu trúc
  persona; đánh giá theo "loại B" (ngưỡng/quan sát), không assert cứng độ chính xác.
- Reply GPT chỉ bật khi cấp `OPENAI_API_KEY`; mặc định chạy reply mẫu (vẫn đúng nghiệp vụ,
  miễn phí). Vector store ngữ nghĩa là thật ở cả hai chế độ.
