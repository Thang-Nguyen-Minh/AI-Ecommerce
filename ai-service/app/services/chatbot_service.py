"""
Chatbot tư vấn (GĐ4) — RAG: retrieval ngữ nghĩa (vector store) → sinh câu trả lời.
Reply Auto: có OPENAI_API_KEY → GPT có grounding (chống bịa); không có → mẫu.
Hạ cấp: vector chết → keyword; catalog chết → popularity (BR-4, TC-10/TC-12).
suggested luôn là sản phẩm CÓ THẬT (BR-7/TC-13).
"""
import logging
import re
import unicodedata

from .. import db, product_client, vector_store
from ..config import OPENAI_API_KEY

logger = logging.getLogger("ai.chatbot")


def _strip_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


STOP = {"toi", "can", "mua", "tim", "co", "khong", "la", "gi", "cho", "mot", "cai",
        "muon", "ban", "nao", "the", "va", "hay", "giup", "minh", "duoc"}


def _keywords(msg: str):
    words = re.findall(r"\w+", _strip_accent(msg))
    return [w for w in words if w not in STOP and len(w) > 1]


def _keyword_retrieve(message, catalog):
    """Fallback truy hồi theo từ khoá (khi vector store chết)."""
    kws = _keywords(message or "")
    cheap = any(k in _strip_accent(message or "") for k in ["re", "gia thap", "tiet kiem"])
    scored = []
    for p in catalog:
        hay = _strip_accent(f"{p.get('name','')} {p.get('category_name','')} {p.get('short_description','')} {p.get('product_type','')}")
        overlap = sum(1 for k in kws if k in hay)
        if overlap:
            scored.append((overlap, -float(p.get("price", 0)) if cheap else float(p.get("sold_count", 0)), p))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [p for _, _, p in scored[:5]]


def _generate_reply(message, products):
    """Sinh câu trả lời. Có OPENAI_API_KEY → GPT (grounding); lỗi/không key → mẫu."""
    names = ", ".join(p["name"] for p in products[:3])
    fallback = f"Dựa trên yêu cầu của bạn, mình gợi ý: {names}."
    if not OPENAI_API_KEY or not products:
        return fallback
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        context = "\n".join(
            f"- {p['name']} (giá {p.get('price')}, loại {p.get('product_type')})" for p in products
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                    "Bạn là trợ lý bán hàng. CHỈ được giới thiệu các sản phẩm trong danh sách dưới. "
                    "Không bịa tên/giá sản phẩm khác. Trả lời ngắn gọn, thân thiện bằng tiếng Việt."},
                {"role": "user", "content": f"Khách hỏi: {message}\n\nSản phẩm có sẵn:\n{context}"},
            ],
            max_tokens=200, temperature=0.3,
        )
        return resp.choices[0].message.content.strip() or fallback
    except Exception as e:
        logger.warning(f"LLM reply error, fallback mẫu: {e}")
        return fallback


def answer(message: str, user_id: int):
    catalog = product_client.get_all_products()

    # BR-4: catalog lỗi → hạ cấp sang phổ biến từ behavior store
    if not catalog:
        pop = product_client.existing_ids([pid for pid, _ in db.popular_products(5)])
        return {
            "reply": "Hệ thống tư vấn tạm bận, đây là vài sản phẩm phổ biến bạn có thể tham khảo.",
            "suggested": pop[:5],
        }

    by_id = {p["id"]: p for p in catalog}

    # 1) Retrieval ngữ nghĩa (RAG)
    hits = vector_store.search(message, k=5)
    top = []
    if hits:
        top = [by_id[pid] for pid, _ in hits if pid in by_id]

    # 2) Fallback keyword nếu vector store chết/rỗng
    if not top:
        top = _keyword_retrieve(message, catalog)

    # 3) Vẫn rỗng → phổ biến, vẫn lịch sự (TC-12)
    if not top:
        top = sorted(catalog, key=lambda p: p.get("sold_count", 0), reverse=True)[:5]
        return {
            "reply": "Mình chưa rõ ý bạn lắm, nhưng đây là vài sản phẩm đang được quan tâm nhiều:",
            "suggested": [p["id"] for p in top],
        }

    return {"reply": _generate_reply(message, top), "suggested": [p["id"] for p in top]}
