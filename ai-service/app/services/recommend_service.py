"""
Hybrid recommender (GĐ1 baseline + GĐ2 sequence + GĐ3 graph + GĐ5 hybrid).

final = W_GRAPH·graph + W_LSTM·sequence(cooccurrence) + W_POP·popularity

Mọi tầng đều chịu lỗi: thành phần con chết → bỏ qua tín hiệu đó, không sập (BR-4).
Cold start (user chưa có hành vi) → popularity → catalog (luôn có gợi ý, BR-1).
"""
from .. import db, graph, lstm_model, product_client
from ..config import W_GRAPH, W_LSTM, W_POP


def _norm(pairs):
    """Chuẩn hoá score về [0,1] để cộng các tín hiệu khác thang đo."""
    if not pairs:
        return {}
    mx = max(s for _, s in pairs) or 1
    return {pid: s / mx for pid, s in pairs}


def recommend(user_id: int, n: int = 5):
    seen = set(db.user_products(user_id))
    scores = {}

    # GĐ3: graph SIMILAR (cá nhân hoá) — bỏ qua nếu Neo4j chết
    for pid, w in _norm(graph.recommend_personalized(user_id, n * 4)).items():
        scores[pid] = scores.get(pid, 0) + W_GRAPH * w

    # GĐ2: LSTM next-item nếu có snapshot, không thì co-occurrence (fallback, BR-4)
    if lstm_model.available():
        recent = [pid for pid, _, _ in reversed(db.user_recent(user_id, 20))]  # chronological
        seq_signal = lstm_model.predict_next(recent, n * 4, exclude=seen)
    else:
        seq_signal = db.cooccurrence(user_id, n * 4)
    for pid, w in _norm(seq_signal).items():
        scores[pid] = scores.get(pid, 0) + W_LSTM * w

    # GĐ1: popularity baseline
    for pid, w in _norm(db.popular_products(n * 6, exclude=seen)).items():
        scores[pid] = scores.get(pid, 0) + W_POP * w

    # Loại sản phẩm đã chạm + xếp hạng
    ranked = [pid for pid, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True) if pid not in seen]

    # Cold start / thiếu dữ liệu → popularity toàn hệ thống (không loại seen)
    if not ranked:
        ranked = [pid for pid, _ in db.popular_products(n * 6)]

    # BR-2: chỉ giữ sản phẩm còn tồn tại; BR-3: không trùng
    ranked = product_client.existing_ids(list(dict.fromkeys(ranked)))

    # Vẫn rỗng (behavior store trống) → lấy từ catalog để LUÔN có gợi ý (BR-1)
    if not ranked:
        ranked = [p["id"] for p in product_client.get_all_products()]

    items = []
    for pid in ranked[:n]:
        items.append({"product_id": pid, "score": round(scores.get(pid, 0.0), 4)})
    return items
