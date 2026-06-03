import logging
import os

import requests
from requests.exceptions import ConnectionError, Timeout

logger = logging.getLogger('cart')

PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:8002')
TIMEOUT_SECONDS = 5  # BR-8: không treo vô hạn


class ProductServiceError(Exception):
    """Lỗi khi gọi product-service."""
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def get_product(product_id: int) -> dict:
    """
    Gọi GET /products/{id}/ trên product-service.
    BR-2: product không tồn tại → ProductServiceError(404)
    BR-8: timeout/sập → ProductServiceError(503)
    Trả dict chứa ít nhất {id, price, stock}.
    """
    url = f"{PRODUCT_SERVICE_URL}/products/{product_id}/"
    try:
        resp = requests.get(url, timeout=TIMEOUT_SECONDS)
    except Timeout:
        logger.error(f"[CART] product-service timeout: {url}")
        raise ProductServiceError("product-service không phản hồi (timeout)", 503)
    except ConnectionError:
        logger.error(f"[CART] product-service unreachable: {url}")
        raise ProductServiceError("product-service không khả dụng", 503)

    if resp.status_code == 404:
        raise ProductServiceError(f"Sản phẩm {product_id} không tồn tại", 404)

    if not resp.ok:
        logger.error(f"[CART] product-service error {resp.status_code}: {url}")
        raise ProductServiceError(f"product-service lỗi ({resp.status_code})", 502)

    return resp.json()
