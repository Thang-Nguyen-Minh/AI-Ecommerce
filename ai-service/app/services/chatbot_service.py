"""
Chatbot tư vấn — LangChain RAG + Google Gemini.
Flow: truy hồi ngữ nghĩa (FAISS) → sinh câu trả lời (Gemini / fallback mẫu).
Hạ cấp: Gemini lỗi/không key → template; vector lỗi → keyword; catalog lỗi → popular.
Sản phẩm gợi ý luôn có thật (BR-7).
"""
import logging
import re
import unicodedata

from .. import db, product_client, vector_store
from ..config import GOOGLE_API_KEY

logger = logging.getLogger("ai.chatbot")

STOP = {"toi", "can", "mua", "tim", "co", "khong", "la", "gi", "cho", "mot", "cai",
        "muon", "ban", "nao", "the", "va", "hay", "giup", "minh", "duoc"}


def _strip_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _keywords(msg: str):
    words = re.findall(r"\w+", _strip_accent(msg))
    return [w for w in words if w not in STOP and len(w) > 1]


def _keyword_retrieve(message, catalog):
    kws = _keywords(message or "")
    cheap = any(k in _strip_accent(message or "") for k in ["re", "gia thap", "tiet kiem"])
    scored = []
    for p in catalog:
        hay = _strip_accent(
            f"{p.get('name','')} {p.get('category_name','')} "
            f"{p.get('short_description','')} {p.get('product_type','')}"
        )
        overlap = sum(1 for k in kws if k in hay)
        if overlap:
            scored.append((overlap, -float(p.get("price", 0)) if cheap else float(p.get("sold_count", 0)), p))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [p for _, _, p in scored[:5]]


# ── LangChain RAG chain (khởi tạo lazy, singleton) ──────────────────────────
_rag_chain = None


def _build_rag_chain():
    """Xây RAG chain với Gemini LLM + FAISS retriever. Trả None nếu lỗi."""
    global _rag_chain
    if _rag_chain is not None:
        return _rag_chain
    if not GOOGLE_API_KEY:
        return None

    vs = vector_store.get_vectorstore()
    if vs is None:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough, RunnableLambda
        from langchain_core.output_parsers import StrOutputParser

        retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        prompt = ChatPromptTemplate.from_template(
            "Bạn là trợ lý bán hàng thân thiện. "
            "CHỈ được giới thiệu sản phẩm có trong danh sách dưới đây. "
            "Không bịa tên/giá sản phẩm khác. "
            "Trả lời ngắn gọn, tự nhiên bằng tiếng Việt.\n\n"
            "Sản phẩm có sẵn:\n{context}\n\n"
            "Khách hỏi: {question}"
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
            max_tokens=300,
        )

        def format_docs(docs):
            return "\n".join(
                f"- {d.metadata.get('name','?')} (ID:{d.metadata.get('product_id','?')}): {d.page_content[:120]}"
                for d in docs
            )

        _rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        logger.info("RAG chain built with Gemini")
        return _rag_chain
    except Exception as e:
        logger.warning(f"_build_rag_chain error: {e}")
        return None


def _generate_reply(message: str, products: list) -> str:
    """Sinh câu trả lời. Ưu tiên: Gemini RAG → Gemini direct → template."""
    names = ", ".join(p["name"] for p in products[:3])
    fallback = f"Dựa trên yêu cầu của bạn, mình gợi ý: {names}."

    # Thử RAG chain với Gemini
    chain = _build_rag_chain()
    if chain:
        try:
            reply = chain.invoke(message)
            return reply.strip() if reply and reply.strip() else fallback
        except Exception as e:
            logger.warning(f"Gemini RAG error, fallback mẫu: {e}")

    # Fallback OpenAI nếu có key
    try:
        from ..config import OPENAI_API_KEY
        if OPENAI_API_KEY:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            context = "\n".join(
                f"- {p['name']} (giá {p.get('price')}, loại {p.get('product_type')})"
                for p in products
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                        "Bạn là trợ lý bán hàng. CHỈ giới thiệu sản phẩm trong danh sách. "
                        "Trả lời ngắn gọn, thân thiện bằng tiếng Việt."},
                    {"role": "user", "content": f"Khách hỏi: {message}\n\nSản phẩm:\n{context}"},
                ],
                max_tokens=200, temperature=0.3,
            )
            return resp.choices[0].message.content.strip() or fallback
    except Exception:
        pass

    return fallback


def answer(message: str, user_id: int):
    catalog = product_client.get_all_products()

    if not catalog:
        pop = product_client.existing_ids([pid for pid, _ in db.popular_products(5)])
        return {
            "reply": "Hệ thống tư vấn tạm bận, đây là vài sản phẩm phổ biến bạn có thể tham khảo.",
            "suggested": pop[:5],
        }

    by_id = {p["id"]: p for p in catalog}

    # 1) Retrieval ngữ nghĩa
    hits = vector_store.search(message, k=5)
    top = []
    if hits:
        top = [by_id[pid] for pid, _ in hits if pid in by_id]

    # 2) Fallback keyword nếu vector store không dùng được
    if not top:
        top = _keyword_retrieve(message, catalog)

    # 3) Vẫn rỗng → phổ biến
    if not top:
        top = sorted(catalog, key=lambda p: p.get("sold_count", 0), reverse=True)[:5]
        return {
            "reply": "Mình chưa rõ ý bạn lắm, nhưng đây là vài sản phẩm đang được quan tâm nhiều:",
            "suggested": [p["id"] for p in top],
        }

    return {
        "reply": _generate_reply(message, top),
        "suggested": [p["id"] for p in top],
    }
