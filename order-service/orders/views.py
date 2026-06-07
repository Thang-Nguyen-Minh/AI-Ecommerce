import logging
from decimal import Decimal

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from .serializers import OrderSerializer
from .services import ServiceError, call_payment, call_shipping, clear_cart, get_cart, get_product

logger = logging.getLogger('orders')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders(request):
    if request.method == 'GET':
        return list_orders(request)
    return create_order(request)


def create_order(request):
    """
    POST /orders/
    BR-1: user_id từ JWT.
    BR-2: giỏ rỗng → 400.
    BR-3: total_price do server tính, bỏ qua giá client gửi.
    BR-4: kiểm tồn kho lúc đặt.
    BR-5: gọi payment → success → gọi shipping.
    BR-7: lỗi payment → PAYMENT_FAILED, không tạo shipment.
    """
    shipping_address = request.data.get('shipping_address', '').strip()
    if not shipping_address:
        return Response({'error': 'shipping_address là bắt buộc'}, status=400)

    recipient_name = request.data.get('recipient_name', '').strip()
    phone = request.data.get('phone', '').strip()

    # Cờ test sandbox (vd "fail") để kiểm chứng TC-09; production payment bỏ qua.
    simulate = request.data.get('simulate')

    # Lấy chuỗi token gốc từ header để forward sang cart
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token_str = auth_header.removeprefix('Bearer ').strip()

    # ── Đọc giỏ hàng (BR-2) ──────────────────────────
    try:
        cart = get_cart(token_str)
    except ServiceError as e:
        return Response({'error': str(e)}, status=e.status_code)

    cart_items = cart.get('items', [])
    if not cart_items:
        return Response({'error': 'Giỏ hàng trống, không thể tạo đơn'}, status=400)

    # ── Lấy giá + kiểm tồn kho (BR-3, BR-4) ─────────
    line_items = []
    total = Decimal('0')
    for ci in cart_items:
        try:
            product = get_product(ci['product_id'])
        except ServiceError as e:
            return Response({'error': str(e)}, status=e.status_code)

        stock = product.get('stock', 0)
        qty = ci['quantity']
        if qty > stock:
            return Response(
                {'error': f"Sản phẩm {ci['product_id']} không đủ hàng (còn {stock}, cần {qty})"},
                status=400,
            )
        unit_price = Decimal(str(product['price']))
        total += unit_price * qty
        line_items.append({'product_id': ci['product_id'], 'quantity': qty, 'unit_price': unit_price})

    # ── Tạo đơn PENDING (BR-3: server tính total) ────
    order = Order.objects.create(
        user_id=request.user.id,
        total_price=total,
        status='PENDING',
        shipping_address=shipping_address,
        recipient_name=recipient_name,
        phone=phone,
    )
    for li in line_items:
        OrderItem.objects.create(order=order, **li)

    logger.info(f"[ORDER] Created order={order.id} user={request.user.id} total={total}")

    # ── Điều phối payment (BR-5, BR-7) ───────────────
    try:
        payment_result = call_payment(order.id, total, token_str, simulate=simulate)
    except ServiceError as e:
        # BR-7: payment KHÔNG phản hồi (sập/timeout) → 503, đơn PAYMENT_FAILED,
        #       tuyệt đối không gọi shipping. Giỏ KHÔNG bị dọn để user thử lại.
        order.status = 'PAYMENT_FAILED'
        order.save()
        logger.warning(f"[ORDER] Payment unreachable order={order.id}: {e}")
        return Response(
            {'error': str(e), 'order': OrderSerializer(order).data},
            status=503,
        )

    payment_status = payment_result.get('status', '').upper()

    if payment_status != 'SUCCESS':
        # Payment phản hồi nhưng từ chối (BR-5): không gọi shipping.
        order.status = 'PAYMENT_FAILED'
        order.save()
        resp = OrderSerializer(order).data
        resp['payment_error'] = 'Thanh toán thất bại'
        return Response(resp, status=status.HTTP_201_CREATED)

    # Payment thành công → PAID
    order.status = 'PAID'
    order.save()

    # ── Shipping chỉ khi payment thành công (BR-5) ──
    # Shipping-service chưa dựng → ServiceError → đơn giữ ở PAID (không nửa vời).
    try:
        call_shipping(order.id, shipping_address, token_str)
        order.status = 'SHIPPED'
        order.save()
    except ServiceError as e:
        logger.warning(f"[ORDER] Shipping chưa sẵn sàng order={order.id}: {e}")

    # Dọn giỏ khi đã thanh toán xong (TC-11: tránh đặt/charge trùng)
    clear_cart(token_str)

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


def list_orders(request):
    # BR-6: khách chỉ xem đơn của mình.
    # Admin/staff có thể xem đơn của một khách qua ?user_id=<id> (để quản lý giao hàng).
    target_user = request.query_params.get('user_id')
    is_staff = getattr(request.user, 'role', None) in ('admin', 'staff')
    if target_user and is_staff:
        qs = Order.objects.filter(user_id=target_user)
    else:
        qs = Order.objects.filter(user_id=request.user.id)
    return Response(OrderSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    """GET /orders/{id} — BR-6: cách ly đơn (admin/staff xem được mọi đơn)."""
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return Response({'error': 'Không tìm thấy đơn hàng'}, status=404)

    is_staff = getattr(request.user, 'role', None) in ('admin', 'staff')
    if order.user_id != request.user.id and not is_staff:
        return Response({'error': 'Không có quyền xem đơn này'}, status=403)

    return Response(OrderSerializer(order).data)
