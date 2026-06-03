import logging

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import IsAdminOrStaff, RemoteUserJWTAuthentication
from .models import Shipment
from .serializers import ShipmentSerializer

logger = logging.getLogger('shipping')


@api_view(['POST'])
@authentication_classes([])      # BR-5: nội bộ, order-service gọi
@permission_classes([AllowAny])
def create_shipment(request):
    """
    POST /shipping/create  Body: {order_id, address}
    BR-1: address bắt buộc. BR-4: idempotent theo order_id.
    """
    order_id = request.data.get('order_id')
    address  = (request.data.get('address') or '').strip()

    if order_id is None:
        return Response({'error': 'order_id là bắt buộc'}, status=400)
    if not address:
        return Response({'error': 'address là bắt buộc'}, status=400)

    # BR-4: đã có phiếu → trả lại, không tạo mới
    existing = Shipment.objects.filter(order_id=order_id).first()
    if existing:
        return Response(ShipmentSerializer(existing).data, status=200)

    shipment = Shipment.objects.create(order_id=order_id, address=address, status='Processing')
    logger.info(f"[SHIPPING] created shipment order={order_id}")
    return Response(ShipmentSerializer(shipment).data, status=201)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def shipment_status(request):
    """GET /shipping/status?order_id=<id>"""
    order_id = request.query_params.get('order_id')
    if not order_id:
        return Response({'error': 'order_id là bắt buộc'}, status=400)

    shipment = Shipment.objects.filter(order_id=order_id).first()
    if not shipment:
        return Response({'error': 'Không có phiếu giao cho order_id này'}, status=404)

    return Response({'order_id': int(order_id), 'status': shipment.status})


@api_view(['PATCH'])
@authentication_classes([RemoteUserJWTAuthentication])
@permission_classes([IsAdminOrStaff])      # BR-5: chỉ staff/admin
def update_shipment(request, pk):
    """PATCH /shipping/<id>  Body: {status} — BR-2: chỉ tiến đúng thứ tự."""
    try:
        shipment = Shipment.objects.get(pk=pk)
    except Shipment.DoesNotExist:
        return Response({'error': 'Không tìm thấy phiếu giao'}, status=404)

    new_status = request.data.get('status')
    if new_status not in dict(Shipment.STATUS_CHOICES):
        return Response({'error': 'status không hợp lệ'}, status=400)

    # BR-2: chỉ cho chuyển theo VALID_TRANSITIONS
    allowed = Shipment.VALID_TRANSITIONS.get(shipment.status, [])
    if new_status != shipment.status and new_status not in allowed:
        return Response(
            {'error': f'Không thể chuyển {shipment.status} → {new_status}'},
            status=400,
        )

    shipment.status = new_status
    shipment.save()
    logger.info(f"[SHIPPING] order={shipment.order_id} → {new_status} by {request.user.username}")
    return Response(ShipmentSerializer(shipment).data)
