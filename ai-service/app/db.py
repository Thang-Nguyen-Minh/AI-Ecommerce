"""Behavior store — SQLite (DB riêng của ai-service, log hành vi user)."""
import os
import sqlite3
import threading

from .config import BEHAVIOR_DB

_lock = threading.Lock()


def _conn():
    os.makedirs(os.path.dirname(BEHAVIOR_DB), exist_ok=True)
    c = sqlite3.connect(BEHAVIOR_DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS behavior_event (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                action     TEXT    NOT NULL,
                ts         REAL    NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_user ON behavior_event(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_product ON behavior_event(product_id)")


def add_event(user_id: int, product_id: int, action: str, ts: float):
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO behavior_event (user_id, product_id, action, ts) VALUES (?,?,?,?)",
            (user_id, product_id, action, ts),
        )


def popular_products(limit: int = 20, exclude=()):
    """Top sản phẩm theo số lượt tương tác (toàn hệ thống) — baseline + cold start."""
    with _conn() as c:
        rows = c.execute("""
            SELECT product_id, COUNT(*) AS cnt
            FROM behavior_event
            GROUP BY product_id
            ORDER BY cnt DESC
        """).fetchall()
    out = [(r["product_id"], r["cnt"]) for r in rows if r["product_id"] not in exclude]
    return out[:limit]


def user_products(user_id: int):
    """Các product_id user đã tương tác (để loại khỏi gợi ý + làm seed cá nhân hóa)."""
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT product_id FROM behavior_event WHERE user_id=?", (user_id,)
        ).fetchall()
    return [r["product_id"] for r in rows]


def user_recent(user_id: int, limit: int = 20):
    """Chuỗi hành vi gần nhất của user (cho tín hiệu LSTM/sequence heuristic)."""
    with _conn() as c:
        rows = c.execute(
            "SELECT product_id, action, ts FROM behavior_event WHERE user_id=? ORDER BY ts DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [(r["product_id"], r["action"], r["ts"]) for r in rows]


def cooccurrence(user_id: int, limit: int = 20):
    """
    Item-based CF từ behavior store: 'người tương tác với SP của bạn cũng tương tác với X'.
    Dùng làm tín hiệu sequence (stand-in cho LSTM) — chạy được cả khi Neo4j chết.
    """
    seen = user_products(user_id)
    if not seen:
        return []
    ph = ",".join("?" * len(seen))
    with _conn() as c:
        rows = c.execute(f"""
            SELECT e2.product_id AS pid, COUNT(DISTINCT e2.user_id) AS cnt
            FROM behavior_event e1
            JOIN behavior_event e2
              ON e2.user_id = e1.user_id AND e2.product_id <> e1.product_id
            WHERE e1.product_id IN ({ph})
              AND e2.product_id NOT IN ({ph})
            GROUP BY e2.product_id
            ORDER BY cnt DESC
            LIMIT ?
        """, (*seen, *seen, limit)).fetchall()
    return [(r["pid"], r["cnt"]) for r in rows]


def all_events():
    """Toàn bộ event (cho batch dựng cạnh Neo4j ở GĐ3)."""
    with _conn() as c:
        rows = c.execute("SELECT user_id, product_id, action FROM behavior_event").fetchall()
    return [(r["user_id"], r["product_id"], r["action"]) for r in rows]


def ordered_sequences():
    """Chuỗi product_id theo thứ tự thời gian cho từng user (train LSTM)."""
    with _conn() as c:
        rows = c.execute(
            "SELECT user_id, product_id FROM behavior_event ORDER BY user_id, ts, id"
        ).fetchall()
    seqs = {}
    for r in rows:
        seqs.setdefault(r["user_id"], []).append(r["product_id"])
    return seqs


def count_events():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) AS n FROM behavior_event").fetchone()["n"]
