#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Kiểm thử đầu-cuối toàn hệ thống ecom-final (contract shipping mục 8)
#  Chứng minh luồng tài liệu 4.7.2: payment success → mới gọi shipping.
#  Yêu cầu: cả 6 service đang chạy (docker compose up -d).
#  Chạy:  bash test-e2e.sh
# ═══════════════════════════════════════════════════════════════
set -u

USER_URL=http://localhost:8001
PROD_URL=http://localhost:8002
CART_URL=http://localhost:8003
ORDER_URL=http://localhost:8004
PAY_URL=http://localhost:8005
SHIP_URL=http://localhost:8006

pass=0; fail=0
ok()   { echo "  ✅ $1"; pass=$((pass+1)); }
bad()  { echo "  ❌ $1"; fail=$((fail+1)); }

# jq thay thế bằng python trong container (không phụ thuộc jq host)
jget() { docker exec -i ecom-user-service python3 -c "import sys,json;print(json.load(sys.stdin).get('$1',''))"; }

echo "════════ CHUẨN BỊ: tài khoản + sản phẩm ════════"
CUST=$(curl -s -X POST $USER_URL/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"khach1@test.com","password":"MatKhau123!"}' | jget access)
[ -n "$CUST" ] && ok "customer login" || { bad "customer login"; exit 1; }

STAFF=$(curl -s -X POST $USER_URL/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"nhanvien1@test.com","password":"NhanVien123!"}' | jget access)
[ -n "$STAFF" ] && ok "staff login" || bad "staff login"

# Chọn 1 product còn hàng
PID=$(curl -s "$PROD_URL/products/?in_stock=1" | docker exec -i ecom-product-service python3 -c "
import sys,json; d=json.load(sys.stdin); r=d.get('results',d)
print(r[0]['id'] if r else '')")
[ -n "$PID" ] && ok "có sản phẩm còn hàng (id=$PID)" || { bad "không có sản phẩm"; exit 1; }

echo ""
echo "════════ KỊCH BẢN THÀNH CÔNG (happy path) ════════"
curl -s -X DELETE $CART_URL/cart/clear -H "Authorization: Bearer $CUST" >/dev/null
curl -s -X POST $CART_URL/cart/add -H "Authorization: Bearer $CUST" \
  -H "Content-Type: application/json" -d "{\"product_id\":$PID,\"quantity\":1}" >/dev/null

RESP=$(curl -s -X POST $ORDER_URL/orders/ -H "Authorization: Bearer $CUST" \
  -H "Content-Type: application/json" -d '{"shipping_address":"123 Le Loi, Ha Noi"}')
OID=$(echo "$RESP" | docker exec -i ecom-order-service python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")
OSTATUS=$(echo "$RESP" | docker exec -i ecom-order-service python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))")

[ "$OSTATUS" = "SHIPPED" ] && ok "đơn #$OID → SHIPPED" || bad "đơn status=$OSTATUS (mong đợi SHIPPED)"

PS=$(curl -s "$PAY_URL/payment/status?order_id=$OID" | docker exec -i ecom-payment-service python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))")
[ "$PS" = "Success" ] && ok "payment → Success" || bad "payment=$PS"

SS=$(curl -s "$SHIP_URL/shipping/status?order_id=$OID" | docker exec -i ecom-shipping-service python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))")
[ "$SS" = "Processing" ] && ok "shipment → Processing" || bad "shipment=$SS"

# Staff đẩy trạng thái
SID=$(curl -s -X POST $SHIP_URL/shipping/create -H "Content-Type: application/json" \
  -d "{\"order_id\":$OID,\"address\":\"-\"}" | docker exec -i ecom-shipping-service python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")
c1=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH $SHIP_URL/shipping/$SID -H "Authorization: Bearer $STAFF" -H "Content-Type: application/json" -d '{"status":"Shipping"}')
c2=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH $SHIP_URL/shipping/$SID -H "Authorization: Bearer $STAFF" -H "Content-Type: application/json" -d '{"status":"Delivered"}')
[ "$c1" = "200" ] && [ "$c2" = "200" ] && ok "staff đẩy Shipping→Delivered" || bad "staff update ($c1,$c2)"

SS2=$(curl -s "$SHIP_URL/shipping/status?order_id=$OID" | docker exec -i ecom-shipping-service python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))")
[ "$SS2" = "Delivered" ] && ok "shipment cuối → Delivered" || bad "shipment=$SS2"

echo ""
echo "════════ KỊCH BẢN THẤT BẠI (fail path) ════════"
curl -s -X DELETE $CART_URL/cart/clear -H "Authorization: Bearer $CUST" >/dev/null
curl -s -X POST $CART_URL/cart/add -H "Authorization: Bearer $CUST" \
  -H "Content-Type: application/json" -d "{\"product_id\":$PID,\"quantity\":1}" >/dev/null

RESP2=$(curl -s -X POST $ORDER_URL/orders/ -H "Authorization: Bearer $CUST" \
  -H "Content-Type: application/json" -d '{"shipping_address":"X","simulate":"fail"}')
OID2=$(echo "$RESP2" | docker exec -i ecom-order-service python3 -c "import sys,json;d=json.load(sys.stdin);o=d.get('order',d);print(o.get('id',''))")
OSTATUS2=$(echo "$RESP2" | docker exec -i ecom-order-service python3 -c "import sys,json;d=json.load(sys.stdin);o=d.get('order',d);print(o.get('status',''))")

[ "$OSTATUS2" = "PAYMENT_FAILED" ] && ok "đơn #$OID2 → PAYMENT_FAILED" || bad "đơn status=$OSTATUS2"

PS2=$(curl -s "$PAY_URL/payment/status?order_id=$OID2" | docker exec -i ecom-payment-service python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))")
[ "$PS2" = "Failed" ] && ok "payment → Failed" || bad "payment=$PS2"

SHIP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SHIP_URL/shipping/status?order_id=$OID2")
[ "$SHIP_CODE" = "404" ] && ok "KHÔNG có shipment (404) — đúng luật 4.7.2" || bad "shipment HTTP=$SHIP_CODE (mong đợi 404)"

echo ""
echo "════════ KẾT QUẢ: PASS=$pass  FAIL=$fail ════════"
[ "$fail" -eq 0 ] && echo "🎉 Toàn hệ thống đúng luồng tài liệu 2.9 / 4.7.2" || echo "⚠️  Có test fail, xem ở trên"
exit $fail
