"""
Knowledge Graph trên Neo4j (GĐ3, tài liệu 3.5).
- Ánh xạ event → cạnh: view/click → VIEW(count), add_to_cart → BUY(count).
- Cypher tính SIMILAR (đồng xuất hiện theo user).
- Truy vấn gợi ý cá nhân hóa + fallback phổ biến.
Mọi hàm chịu lỗi: Neo4j chết → trả [] / False, KHÔNG raise (BR-4).
"""
import logging
import time

from .config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

logger = logging.getLogger("ai.graph")

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

_driver = None
# Cache trạng thái Neo4j để KHÔNG thử kết nối (treo) mỗi request khi nó chết (BR-4, độ trễ)
_ok = False
_last_check = 0
_CHECK_TTL = 15


def _get_driver():
    global _driver
    if GraphDatabase is None:
        return None
    if _driver is None:
        try:
            # Timeout ngắn → fail nhanh khi Neo4j down (không treo /events)
            _driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=2, connection_acquisition_timeout=2,
                max_transaction_retry_time=2,
            )
        except Exception as e:
            logger.warning(f"Neo4j driver init failed: {e}")
            return None
    return _driver


def available() -> bool:
    """Có cache: chỉ ping Neo4j tối đa mỗi _CHECK_TTL giây."""
    global _ok, _last_check
    now = time.time()
    if now - _last_check < _CHECK_TTL:
        return _ok
    _last_check = now
    d = _get_driver()
    if not d:
        _ok = False
        return False
    try:
        with d.session() as s:
            s.run("RETURN 1").consume()
        _ok = True
    except Exception:
        _ok = False
    return _ok


def record_event(user_id: int, product_id: int, action: str):
    """Ghi cạnh live khi event tới (cộng dồn count). Bỏ qua nhanh nếu Neo4j chết."""
    if not available():   # cache → không treo khi Neo4j down
        return
    d = _get_driver()
    if not d:
        return
    rel = "BUY" if action == "add_to_cart" else "VIEW"
    try:
        with d.session() as s:
            s.run(
                f"""
                MERGE (u:User {{id:$uid}})
                MERGE (p:Product {{id:$pid}})
                MERGE (u)-[r:{rel}]->(p)
                SET r.count = coalesce(r.count,0)+1
                """,
                uid=user_id, pid=product_id,
            )
    except Exception as e:
        logger.warning(f"record_event graph error: {e}")


def rebuild_from_events(events):
    """Batch: dựng lại toàn bộ cạnh VIEW/BUY từ behavior store (GĐ3)."""
    d = _get_driver()
    if not d:
        return False
    try:
        with d.session() as s:
            s.run("MATCH (n) DETACH DELETE n")
            for uid, pid, action in events:
                rel = "BUY" if action == "add_to_cart" else "VIEW"
                s.run(
                    f"""
                    MERGE (u:User {{id:$uid}})
                    MERGE (p:Product {{id:$pid}})
                    MERGE (u)-[r:{rel}]->(p)
                    SET r.count = coalesce(r.count,0)+1
                    """,
                    uid=uid, pid=pid,
                )
        return True
    except Exception as e:
        logger.warning(f"rebuild_from_events error: {e}")
        return False


def compute_similar(threshold: int = 5):
    """Tính cạnh SIMILAR = đồng xuất hiện bởi cùng user (>= threshold)."""
    d = _get_driver()
    if not d:
        return False
    try:
        with d.session() as s:
            s.run("MATCH ()-[r:SIMILAR]-() DELETE r")
            s.run(
                """
                MATCH (u:User)-[:VIEW|BUY]->(p1:Product)
                MATCH (u)-[:VIEW|BUY]->(p2:Product)
                WHERE id(p1) < id(p2)
                WITH p1, p2, count(DISTINCT u) AS co
                WHERE co >= $th
                MERGE (p1)-[srel:SIMILAR]-(p2)
                SET srel.weight = co
                """,
                th=threshold,
            )
        return True
    except Exception as e:
        logger.warning(f"compute_similar error: {e}")
        return False


def recommend_personalized(user_id: int, n: int = 5):
    """Gợi ý theo graph: từ sản phẩm đã chạm → SIMILAR chưa chạm. [] nếu lỗi/rỗng."""
    d = _get_driver()
    if not d:
        return []
    try:
        with d.session() as s:
            rows = s.run(
                """
                MATCH (u:User {id:$uid})-[:VIEW|BUY]->(:Product)-[srel:SIMILAR]-(rec:Product)
                WHERE NOT (u)-[:VIEW|BUY]->(rec)
                RETURN rec.id AS product_id, sum(srel.weight) AS score
                ORDER BY score DESC LIMIT $n
                """,
                uid=user_id, n=n,
            )
            return [(r["product_id"], float(r["score"])) for r in rows]
    except Exception as e:
        logger.warning(f"recommend_personalized error: {e}")
        return []


def popular(n: int = 5):
    """Fallback phổ biến từ graph."""
    d = _get_driver()
    if not d:
        return []
    try:
        with d.session() as s:
            rows = s.run(
                """
                MATCH (:User)-[r:VIEW|BUY]->(p:Product)
                RETURN p.id AS product_id, count(r) AS pop
                ORDER BY pop DESC LIMIT $n
                """,
                n=n,
            )
            return [(r["product_id"], float(r["pop"])) for r in rows]
    except Exception as e:
        logger.warning(f"popular graph error: {e}")
        return []


def stats():
    d = _get_driver()
    if not d:
        return {"available": False}
    try:
        with d.session() as s:
            users = s.run("MATCH (u:User) RETURN count(u) AS n").single()["n"]
            prods = s.run("MATCH (p:Product) RETURN count(p) AS n").single()["n"]
            sim = s.run("MATCH ()-[r:SIMILAR]-() RETURN count(r) AS n").single()["n"]
        return {"available": True, "users": users, "products": prods, "similar_edges": sim}
    except Exception:
        return {"available": False}
