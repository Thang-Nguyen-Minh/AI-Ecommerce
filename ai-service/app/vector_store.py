"""
RAG vector store — LangChain + Google Gemini embeddings + FAISS.
Fallback: nếu không có GOOGLE_API_KEY thì dùng sentence-transformers (HuggingFace).
Lazy + singleton. Index persist ở ai_data/vector/ (gitignored).
"""
import json
import logging
import os
import unicodedata

from . import product_client
from .config import EMBED_MODEL, GOOGLE_API_KEY, VECTOR_DIR

logger = logging.getLogger("ai.vector")

_vectorstore = None   # LangChain FAISS object
_ids = None           # list[product_id] theo thứ tự index
_INDEX_PATH = os.path.join(VECTOR_DIR, "index.faiss")
_IDS_PATH   = os.path.join(VECTOR_DIR, "ids.json")


def _get_embeddings():
    """Trả embedding model: Gemini nếu có key, HuggingFace nếu không."""
    if GOOGLE_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=GOOGLE_API_KEY,
        )
    # Fallback: sentence-transformers (không cần key)
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def _product_text(p: dict) -> str:
    parts = [p.get("name", ""), p.get("short_description", ""), p.get("description", ""),
             p.get("category_name", ""), p.get("product_type", "")]
    for key in ("book_detail", "electronics_detail", "fashion_detail"):
        d = p.get(key) or {}
        parts += [str(v) for v in d.values() if v]
    return " ".join(str(x) for x in parts if x)


def build_index():
    """Dựng FAISS index từ catalog. Trả số sản phẩm đã index."""
    from langchain.schema import Document
    from langchain_community.vectorstores import FAISS

    products = product_client.get_all_products()
    if not products:
        logger.warning("build_index: catalog rỗng")
        return 0

    docs = [
        Document(
            page_content=_product_text(p),
            metadata={"product_id": p["id"], "name": p.get("name", "")},
        )
        for p in products
    ]

    try:
        embeddings = _get_embeddings()
        vs = FAISS.from_documents(docs, embeddings)
        os.makedirs(VECTOR_DIR, exist_ok=True)
        vs.save_local(VECTOR_DIR)
        # Lưu map index → product_id
        with open(_IDS_PATH, "w") as f:
            json.dump([p["id"] for p in products], f)

        global _vectorstore, _ids
        _vectorstore = vs
        _ids = [p["id"] for p in products]
        logger.info(f"build_index: {len(_ids)} sản phẩm (Gemini={'yes' if GOOGLE_API_KEY else 'no'})")
        return len(_ids)
    except Exception as e:
        logger.warning(f"build_index error: {e}")
        return 0


def _load():
    """Nạp index từ đĩa. Trả True nếu sẵn sàng."""
    global _vectorstore, _ids
    if _vectorstore is not None and _ids is not None:
        return True
    if not (os.path.exists(os.path.join(VECTOR_DIR, "index.faiss")) and
            os.path.exists(_IDS_PATH)):
        return False
    try:
        from langchain_community.vectorstores import FAISS
        embeddings = _get_embeddings()
        _vectorstore = FAISS.load_local(
            VECTOR_DIR, embeddings, allow_dangerous_deserialization=True
        )
        with open(_IDS_PATH) as f:
            _ids = json.load(f)
        return True
    except Exception as e:
        logger.warning(f"_load vector index error: {e}")
        return False


def ensure_index():
    """Best-effort lúc startup: nếu chưa có index thì dựng."""
    try:
        if not _load():
            build_index()
    except Exception as e:
        logger.warning(f"ensure_index error: {e}")


def search(query: str, k: int = 5):
    """
    Tìm kiếm ngữ nghĩa → [(product_id, score)].
    Trả None nếu vector store không khả dụng (chatbot fallback keyword).
    """
    if not query or not query.strip():
        return None
    if not _load():
        return None
    try:
        results = _vectorstore.similarity_search_with_relevance_scores(query, k=k * 2)
        pairs = [(doc.metadata["product_id"], float(score)) for doc, score in results]
        keep = set(product_client.existing_ids([pid for pid, _ in pairs]))
        return [(pid, sc) for pid, sc in pairs if pid in keep][:k]
    except Exception as e:
        logger.warning(f"vector search error: {e}")
        return None


def get_vectorstore():
    """Trả LangChain FAISS object để dùng trong RAG chain (chatbot_service)."""
    if not _load():
        return None
    return _vectorstore


def stats():
    ready = _load()
    return {
        "ready": ready,
        "count": len(_ids) if (ready and _ids) else 0,
        "engine": "gemini" if GOOGLE_API_KEY else "huggingface",
    }
