"""
RAG vector store (GĐ4 thật) — embed mô tả sản phẩm bằng sentence-transformers +
FAISS (cosine qua inner-product trên vector đã normalize).

Lazy + singleton (giữ độ trễ). Chịu lỗi: model/index lỗi → search() trả None → chatbot
hạ cấp sang keyword (BR-4). Index persist ở ai_data/vector/ (gitignored).
"""
import json
import logging
import os

from . import product_client
from .config import EMBED_MODEL, VECTOR_DIR

logger = logging.getLogger("ai.vector")

_model = None
_index = None
_ids = None          # vị trí trong index -> product_id
_INDEX_PATH = os.path.join(VECTOR_DIR, "index.faiss")
_IDS_PATH = os.path.join(VECTOR_DIR, "ids.json")


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model {EMBED_MODEL} ...")
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _product_text(p: dict) -> str:
    parts = [p.get("name", ""), p.get("short_description", ""), p.get("description", ""),
             p.get("category_name", ""), p.get("product_type", "")]
    for key in ("book_detail", "electronics_detail", "fashion_detail"):
        d = p.get(key) or {}
        parts += [str(v) for v in d.values() if v]
    return " ".join(str(x) for x in parts if x)


def build_index():
    """Dựng FAISS index từ catalog product-service. Trả số sản phẩm đã index."""
    import faiss
    import numpy as np

    products = product_client.get_all_products()
    if not products:
        logger.warning("build_index: catalog rỗng")
        return 0

    model = _get_model()
    texts = [_product_text(p) for p in products]
    emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    emb = np.asarray(emb, dtype="float32")

    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    ids = [p["id"] for p in products]

    os.makedirs(VECTOR_DIR, exist_ok=True)
    faiss.write_index(index, _INDEX_PATH)
    with open(_IDS_PATH, "w") as f:
        json.dump(ids, f)

    global _index, _ids
    _index, _ids = index, ids
    logger.info(f"build_index: {len(ids)} sản phẩm")
    return len(ids)


def _load():
    """Nạp index từ đĩa (nếu có). Trả True nếu sẵn sàng."""
    global _index, _ids
    if _index is not None and _ids is not None:
        return True
    if not (os.path.exists(_INDEX_PATH) and os.path.exists(_IDS_PATH)):
        return False
    try:
        import faiss
        _index = faiss.read_index(_INDEX_PATH)
        with open(_IDS_PATH) as f:
            _ids = json.load(f)
        return True
    except Exception as e:
        logger.warning(f"_load vector index error: {e}")
        return False


def ensure_index():
    """Best-effort lúc startup: nếu chưa có index trên đĩa thì dựng."""
    try:
        if not _load():
            build_index()
    except Exception as e:
        logger.warning(f"ensure_index error: {e}")


def search(query: str, k: int = 5):
    """
    Tìm kiếm ngữ nghĩa → [(product_id, score)] (chỉ sản phẩm còn tồn tại — BR-2).
    Trả None nếu vector store không khả dụng (để chatbot fallback keyword).
    """
    if not query or not query.strip():
        return None
    if not _load():
        return None
    try:
        import numpy as np
        q = _get_model().encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")
        scores, idxs = _index.search(q, min(k * 2, len(_ids)))
        pairs = []
        for pos, sc in zip(idxs[0], scores[0]):
            if 0 <= pos < len(_ids):
                pairs.append((_ids[pos], float(sc)))
        keep = set(product_client.existing_ids([pid for pid, _ in pairs]))
        return [(pid, sc) for pid, sc in pairs if pid in keep][:k]
    except Exception as e:
        logger.warning(f"vector search error: {e}")
        return None


def stats():
    ready = _load()
    return {"ready": ready, "count": len(_ids) if (ready and _ids) else 0}
