import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import CartSerializer
from .services import ProductServiceError, get_product

logger = logging.getLogger('cart')


def _get_or_create_cart(user_id: int) -> Cart:
    """BR-1: mỗi user đúng một giỏ."""
    cart, _ = Cart.objects.get_or_create(user_id=user_id)
    return cart


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    """GET /cart/ — BR-7: token bắt buộc. BR-6: chỉ thấy giỏ của mình."""
    cart = _get_or_create_cart(request.user.id)
    return Response(CartSerializer(cart).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """
    POST /cart/add
    Body: {product_id, quantity}
    BR-1: user_id luôn từ JWT.
    BR-2: gọi product-service để xác nhận sản phẩm tồn tại.
    BR-3: quantity >= 1.
    BR-4: total quantity <= stock.
    BR-5: cộng dồn nếu đã có.
    BR-8: timeout → 503.
    """
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity')

    if not product_id:
        return Response({'error': 'product_id là bắt buộc'}, status=400)

    # BR-3
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return Response({'error': 'quantity phải là số nguyên'}, status=400)
    if quantity < 1:
        return Response({'error': 'quantity phải >= 1'}, status=400)

    # BR-2 + BR-4: gọi product-service
    try:
        product = get_product(int(product_id))
    except ProductServiceError as e:
        return Response({'error': str(e)}, status=e.status_code)

    stock = product.get('stock', 0)
    cart = _get_or_create_cart(request.user.id)

    # BR-5: kiểm tra dòng hiện có
    existing = cart.items.filter(product_id=product_id).first()
    current_qty = existing.quantity if existing else 0
    new_qty = current_qty + quantity

    # BR-4
    if new_qty > stock:
        return Response(
            {'error': f'Vượt tồn kho. Còn {stock} sản phẩm, giỏ đã có {current_qty}.'},
            status=400,
        )

    if existing:
        existing.quantity = new_qty
        existing.save()
    else:
        CartItem.objects.create(cart=cart, product_id=product_id, quantity=quantity)

    logger.info(f"[CART] user={request.user.id} add product={product_id} qty={quantity}")
    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_cart(request):
    """
    PATCH /cart/update
    Body: {product_id, quantity}
    Đặt lại quantity (không cộng dồn). BR-3, BR-4.
    """
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity')

    if not product_id:
        return Response({'error': 'product_id là bắt buộc'}, status=400)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return Response({'error': 'quantity phải là số nguyên'}, status=400)
    if quantity < 1:
        return Response({'error': 'quantity phải >= 1'}, status=400)

    # BR-4: kiểm tra tồn kho
    try:
        product = get_product(int(product_id))
    except ProductServiceError as e:
        return Response({'error': str(e)}, status=e.status_code)

    stock = product.get('stock', 0)
    if quantity > stock:
        return Response({'error': f'Vượt tồn kho. Chỉ còn {stock}.'}, status=400)

    cart = _get_or_create_cart(request.user.id)
    item = cart.items.filter(product_id=product_id).first()
    if not item:
        return Response({'error': 'Sản phẩm không có trong giỏ'}, status=404)

    item.quantity = quantity
    item.save()
    return Response(CartSerializer(cart).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    """
    DELETE /cart/remove
    Body: {product_id}
    BR-6: chỉ xóa trong giỏ của mình.
    """
    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'error': 'product_id là bắt buộc'}, status=400)

    cart = _get_or_create_cart(request.user.id)
    deleted, _ = cart.items.filter(product_id=product_id).delete()
    if not deleted:
        return Response({'error': 'Sản phẩm không có trong giỏ'}, status=404)

    logger.info(f"[CART] user={request.user.id} remove product={product_id}")
    return Response(CartSerializer(cart).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """DELETE /cart/clear — xóa toàn bộ giỏ."""
    cart = _get_or_create_cart(request.user.id)
    cart.items.all().delete()
    return Response(CartSerializer(cart).data)
