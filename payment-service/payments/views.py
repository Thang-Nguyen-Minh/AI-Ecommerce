import logging
import os
from decimal import Decimal, InvalidOperation

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Payment
from .serializers import PaymentSerializer

logger = logging.getLogger('payments')


def _sandbox_enabled():
    return os.environ.get('PAYMENT_SANDBOX', 'true').lower() == 'true'


@api_view(['POST'])
@authentication_classes([])      # BR-4: nội bộ, không cần token người dùng
@permission_classes([AllowAny])
def pay(request):
    """
    POST /payment/pay
    Body: {order_id, amount, simulate?}
    BR-2: amount > 0.
    BR-3 + BR-5: order_id đã có giao dịch → trả lại bản ghi cũ (không tạo mới, không ghi đè).
    BR-6: sandbox — simulate="fail" → Failed; mặc định Success.
    """
    order_id   = request.data.get('order_id')
    amount_raw = request.data.get('amount')
    simulate   = request.data.get('simulate')

    if order_id is None:
        return Response({'error': 'order_id là bắt buộc'}, status=400)

    # BR-2
    try:
        amount = Decimal(str(amount_raw))
    except (InvalidOperation, TypeError):
        return Response({'error': 'amount không hợp lệ'}, status=400)
    if amount <= 0:
        return Response({'error': 'amount phải lớn hơn 0'}, status=400)

    # BR-3, BR-5: idempotent theo order_id, trạng thái cuối không đổi
    existing = Payment.objects.filter(order_id=order_id).first()
    if existing:
        return Response(PaymentSerializer(existing).data, status=200)

    # BR-6: sandbox điều khiển kết quả để test nhánh lỗi
    if _sandbox_enabled() and simulate == 'fail':
        status_val = 'Failed'
    else:
        status_val = 'Success'

    payment = Payment.objects.create(order_id=order_id, amount=amount, status=status_val)
    logger.info(f"[PAYMENT] order={order_id} amount={amount} → {status_val}")
    return Response(PaymentSerializer(payment).data, status=201)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def payment_status(request):
    """GET /payment/status?order_id=<id>"""
    order_id = request.query_params.get('order_id')
    if not order_id:
        return Response({'error': 'order_id là bắt buộc'}, status=400)

    payment = Payment.objects.filter(order_id=order_id).first()
    if not payment:
        return Response({'error': 'Không có giao dịch cho order_id này'}, status=404)

    return Response({'order_id': int(order_id), 'status': payment.status})
