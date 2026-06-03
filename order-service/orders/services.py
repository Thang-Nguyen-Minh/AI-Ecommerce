import logging
import os

import requests
from requests.exceptions import ConnectionError, Timeout

logger = logging.getLogger('orders')
TIMEOUT = 5

CART_SERVICE_URL    = os.environ.get('CART_SERVICE_URL',    'http://localhost:8003')
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:8002')
PAYMENT_SERVICE_URL = os.environ.get('PAYMENT_SERVICE_URL', 'http://localhost:8005')
SHIPPING_SERVICE_URL = os.environ.get('SHIPPING_SERVICE_URL', 'http://localhost:8006')


class ServiceError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def _get(url, headers=None):
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
    except Timeout:
        raise ServiceError(f"Timeout khi gọi {url}", 503)
    except ConnectionError:
        raise ServiceError(f"Không kết nối được {url}", 503)
    return r


def _post(url, data, headers=None):
    try:
        r = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
    except Timeout:
        raise ServiceError(f"Timeout khi gọi {url}", 503)
    except ConnectionError:
        raise ServiceError(f"Không kết nối được {url}", 503)
    return r


def get_cart(token: str) -> dict:
    """Đọc giỏ hàng của user từ cart-service. BR-2."""
    r = _get(f"{CART_SERVICE_URL}/cart/", headers={'Authorization': f'Bearer {token}'})
    if not r.ok:
        raise ServiceError("Không đọc được giỏ hàng", r.status_code)
    return r.json()


def get_product(product_id: int) -> dict:
    """Lấy giá + tồn kho từ product-service. BR-3, BR-4."""
    r = _get(f"{PRODUCT_SERVICE_URL}/products/{product_id}/")
    if r.status_code == 404:
        raise ServiceError(f"Sản phẩm {product_id} không tồn tại", 400)
    if not r.ok:
        raise ServiceError(f"Lỗi product-service ({r.status_code})", 502)
    return r.json()


def call_payment(order_id: int, amount, token: str) -> dict:
    """
    Gọi payment-service. BR-5.
    Trả về dict với 'status' = 'SUCCESS' | 'FAILED'.
    Khi payment-service chưa dựng → ServiceError(503).
    """
    r = _post(
        f"{PAYMENT_SERVICE_URL}/payments/",
        {'order_id': order_id, 'amount': str(amount)},
        headers={'Authorization': f'Bearer {token}'},
    )
    if not r.ok:
        raise ServiceError(f"payment-service lỗi ({r.status_code})", r.status_code)
    return r.json()


def call_shipping(order_id: int, shipping_address: str, token: str) -> dict:
    """
    Gọi shipping-service. Chỉ gọi sau khi payment thành công (BR-5).
    """
    r = _post(
        f"{SHIPPING_SERVICE_URL}/shipments/",
        {'order_id': order_id, 'shipping_address': shipping_address},
        headers={'Authorization': f'Bearer {token}'},
    )
    if not r.ok:
        raise ServiceError(f"shipping-service lỗi ({r.status_code})", r.status_code)
    return r.json()


def clear_cart(token: str):
    """Dọn giỏ sau khi tạo đơn thành công (TC-11: tránh đặt trùng)."""
    try:
        requests.delete(
            f"{CART_SERVICE_URL}/cart/clear",
            headers={'Authorization': f'Bearer {token}'},
            timeout=TIMEOUT,
        )
    except Exception:
        pass  # dọn giỏ không phải critical path
