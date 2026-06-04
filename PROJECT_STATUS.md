# Trạng thái dự án ecom-final

> Cập nhật: sau khi hoàn thành Chương 3 (ai-service) với RAG + LSTM thật.

## Tổng quan: 7/7 microservice cốt lõi đã xong, có git tag nghiệm thu

| Service | Cổng | DB | Chức năng | Tag | Trạng thái |
|---------|------|----|-----------|-----|------------|
| user-service | 8001 | MySQL | Auth, JWT, user, địa chỉ, RBAC | — | ✅ TC pass |
| product-service | 8002 | PostgreSQL | Sản phẩm, danh mục (book/electronics/fashion) | `product-service-ok` | ✅ TC-01→11 |
| cart-service | 8003 | MySQL | Giỏ hàng, gọi product-service | `cart-service-ok` | ✅ TC-01→11 |
| order-service | 8004 | PostgreSQL | Đơn hàng, điều phối payment→shipping | `order-service-ok` | ✅ TC-01→11 |
| payment-service | 8005 | MySQL | Thanh toán (sandbox), idempotent | `payment-service-ok` | ✅ TC-01→07 |
| shipping-service | 8006 | MySQL | Giao hàng, RBAC staff | `shipping-service-ok` | ✅ TC-01→09 |
| ai-service | 8007 | SQLite + Neo4j + FAISS | Gợi ý hybrid + chatbot RAG | `ai-service-ok` | ✅ TC-01→14 |
| frontend + gateway | 80 | — | UI tĩnh + Nginx | — | ✅ |

## Đang ở bước nào?

**Đã hoàn thành toàn bộ luồng nghiệp vụ cốt lõi + AI (Chương 3).**

- Kiểm thử đầu-cuối toàn hệ thống (`test-e2e.sh`): **11/11 PASS** — happy path (đặt hàng →
  thanh toán → giao hàng → Delivered) và fail path (payment fail → không giao hàng).
- ai-service: gợi ý cá nhân hoá (graph + LSTM + popularity), chatbot RAG ngữ nghĩa, 755 events
  + đồ thị tri thức Neo4j (xem `ai-service/knowledge_base/`).

## Luồng đã chứng minh chạy đúng (tài liệu 2.9 / 4.7.2)

```
Đăng nhập → xem sản phẩm (track view → graph) → thêm giỏ → đặt hàng
   → payment Success → tạo shipment (Processing) → staff đẩy Shipping → Delivered
   → gợi ý "đúng gu" + chatbot tư vấn theo catalog thật
Nhánh lỗi: payment Failed → đơn PAYMENT_FAILED, KHÔNG có shipment
```

## Tài liệu tham khảo nhanh

- `ai-service/CHUONG3_TONGKET.md` — tổng kết Chương 3
- `ai-service/knowledge_base/` — dữ liệu thật (755 events + graph) ở dạng CSV
- `*/contract_*.md` + `*/README.md` — hợp đồng & cách chạy từng service
- `test-e2e.sh` — kiểm thử đầu-cuối
- `COMMIT_CONVENTION.md` — quy ước commit

## Phần mở rộng còn có thể làm (không bắt buộc cho đồ án)

- Bật reply GPT cho chatbot (cấp `OPENAI_API_KEY`) — hiện chạy reply mẫu + RAG ngữ nghĩa.
- Tài khoản admin/seed nhiều hơn, tinh chỉnh trọng số hybrid, train LSTM trên dữ liệu lớn hơn.
- Dọn block `/api/payments/` thừa trong `gateway/nginx.conf`.
