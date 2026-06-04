"""
Xác thực JWT do user-service cấp — verify HS256 thủ công (không cần PyJWT),
dùng chung SECRET_KEY. Lấy user_id + role từ claim, không tra DB.
"""
import base64
import hashlib
import hmac
import json
import time

from fastapi import Header, HTTPException

from .config import SECRET_KEY


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def decode_jwt(token: str) -> dict:
    """Verify chữ ký HS256 + hạn dùng, trả payload. Raise ValueError nếu sai."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Token không đúng định dạng")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Chữ ký token không hợp lệ")

    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp") and payload["exp"] < time.time():
        raise ValueError("Token đã hết hạn")
    return payload


class CurrentUser:
    def __init__(self, payload: dict):
        self.id = payload.get("user_id")
        self.username = payload.get("username", "")
        self.role = payload.get("role", "customer")


def get_current_user(authorization: str = Header(default="")) -> CurrentUser:
    """FastAPI dependency: bắt buộc Bearer token hợp lệ (TC-03 → 401 nếu thiếu)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai token")
    token = authorization[7:].strip()
    try:
        payload = decode_jwt(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if not payload.get("user_id"):
        raise HTTPException(status_code=401, detail="Token thiếu user_id")
    return CurrentUser(payload)
