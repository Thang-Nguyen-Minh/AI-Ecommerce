"""
Chatbot tư vấn (GĐ4) — retrieval trên catalog product-service.
Không dùng LLM (OPENAI_API_KEY trống) → trả lời theo mẫu + sản phẩm CÓ THẬT (BR-7).
Hạ cấp lịch sự khi catalog không khả dụng (BR-4, TC-10/TC-12).
"""
import re
import unicodedata

from .. import db, product_client


def _strip_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


STOP = {"toi", "can", "mua", "tim", "co", "khong", "la", "gi", "cho", "mot", "cai",
        "muon", "ban", "nao", "the", "va", "hay", "giup", "minh", "duoc"}


def _keywords(msg: str):
    words = re.findall(r"\w+", _strip_accent(msg))
    return [w for w in words if w not in STOP and len(w) > 1]


def answer(message: str, user_id: int):
    catalog = product_client.get_all_products()

    # BR-4: catalog lỗi → hạ cấp sang phổ biến từ behavior store
    if not catalog:
        pop = product_client.existing_ids([pid for pid, _ in db.popular(5)])
        return {
            "reply": "Hệ thống tư vấn tạm bận, đây là vài sản phẩm phổ biến bạn có thể tham khảo.",
            "suggested": pop[:5],
        }

    kws = _keywords(message or "")
    cheap = any(k in _strip_accent(message or "") for k in ["re", "gia thap", "tiet kiem"])

    scored = []
    for p in catalog:
        hay = _strip_accent(f"{p.get('name','')} {p.get('category_name','')} {p.get('short_description','')} {p.get('product_type','')}")
        overlap = sum(1 for k in kws if k in hay)
        if overlap:
            scored.append((overlap, -float(p.get("price", 0)) if cheap else float(p.get("sold_count", 0)), p))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top = [p for _, _, p in scored[:5]]

    if not top:
        # Không khớp từ khoá → gợi ý phổ biến, vẫn lịch sự (TC-12)
        top = sorted(catalog, key=lambda p: p.get("sold_count", 0), reverse=True)[:5]
        reply = "Mình chưa rõ ý bạn lắm, nhưng đây là vài sản phẩm đang được quan tâm nhiều:"
    else:
        names = ", ".join(p["name"] for p in top[:3])
        reply = f"Dựa trên yêu cầu của bạn, mình gợi ý: {names}."

    return {"reply": reply, "suggested": [p["id"] for p in top]}
