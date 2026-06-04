"""Gọi product-service để xác minh sản phẩm tồn tại (BR-2) và lấy catalog cho chatbot."""
import time

import requests

from .config import PRODUCT_SERVICE_URL

_TIMEOUT = 4
_cache = {"all": None, "ts": 0}
_CACHE_TTL = 60


def product_exists(product_id: int) -> bool:
    try:
        r = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}/", timeout=_TIMEOUT)
        return r.status_code == 200
    except requests.RequestException:
        return False


def get_all_products():
    """Lấy toàn bộ sản phẩm (gom hết các trang). Cache 60s. Trả [] nếu lỗi."""
    if _cache["all"] is not None and time.time() - _cache["ts"] < _CACHE_TTL:
        return _cache["all"]
    items, page = [], 1
    try:
        while True:
            r = requests.get(f"{PRODUCT_SERVICE_URL}/products/?page={page}", timeout=_TIMEOUT)
            if r.status_code != 200:
                break
            data = r.json()
            results = data.get("results", data if isinstance(data, list) else [])
            items.extend(results)
            if not data.get("next"):
                break
            page += 1
    except requests.RequestException:
        return _cache["all"] or []
    _cache["all"] = items
    _cache["ts"] = time.time()
    return items


def existing_ids(candidate_ids):
    """Lọc các id còn tồn tại, giữ thứ tự (dùng catalog cache cho nhanh)."""
    catalog = {p["id"] for p in get_all_products()}
    if catalog:
        return [pid for pid in candidate_ids if pid in catalog]
    # Fallback: catalog rỗng (product-service lỗi) → kiểm từng cái
    return [pid for pid in candidate_ids if product_exists(pid)]
