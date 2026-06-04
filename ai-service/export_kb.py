"""
Xuất knowledge base ra file CSV xem được (mục đích minh bạch dữ liệu).
Chạy: docker exec -e ADMIN_TOKEN=<token> ecom-ai-service python export_kb.py
Ghi vào /app/knowledge_base (host: ai-service/knowledge_base/).
"""
import csv
import os
import sqlite3

import requests

from app.config import BEHAVIOR_DB, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

OUT = "/app/knowledge_base"
os.makedirs(OUT, exist_ok=True)


def export_behavior():
    c = sqlite3.connect(BEHAVIOR_DB)
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT id, user_id, product_id, action, ts FROM behavior_event ORDER BY id").fetchall()
    with open(f"{OUT}/behavior_events.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "user_id", "product_id", "action", "ts"])
        for r in rows:
            w.writerow([r["id"], r["user_id"], r["product_id"], r["action"], r["ts"]])
    # summary
    with open(f"{OUT}/behavior_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Tổng số events: {len(rows)}\n")
        f.write(f"Số user có hành vi: {len(set(r['user_id'] for r in rows))}\n\n")
        by_action = {}
        for r in rows:
            by_action[r["action"]] = by_action.get(r["action"], 0) + 1
        f.write("Theo action:\n")
        for a, n in by_action.items():
            f.write(f"  {a}: {n}\n")
    print(f"  behavior_events.csv ({len(rows)} dòng) + behavior_summary.txt")
    return len(rows)


def export_graph():
    from neo4j import GraphDatabase
    d = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), connection_timeout=5)
    with d.session() as s:
        edges = s.run("MATCH (u:User)-[r:VIEW|BUY]->(p:Product) "
                      "RETURN u.id AS user_id, type(r) AS rel, p.id AS product_id, r.count AS count "
                      "ORDER BY u.id, p.id").data()
        sim = s.run("MATCH (p1:Product)-[r:SIMILAR]-(p2:Product) WHERE p1.id < p2.id "
                    "RETURN p1.id AS a, p2.id AS b, r.weight AS weight ORDER BY weight DESC").data()
    with open(f"{OUT}/graph_edges_view_buy.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["user_id", "rel", "product_id", "count"])
        for e in edges: w.writerow([e["user_id"], e["rel"], e["product_id"], e["count"]])
    with open(f"{OUT}/graph_similar.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["product_a", "product_b", "weight"])
        for e in sim: w.writerow([e["a"], e["b"], e["weight"]])
    print(f"  graph_edges_view_buy.csv ({len(edges)}) + graph_similar.csv ({len(sim)})")


def export_accounts():
    token = os.environ.get("ADMIN_TOKEN")
    if not token:
        print("  (bỏ qua accounts.csv — không có ADMIN_TOKEN)")
        return
    r = requests.get("http://user-service:8000/users/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    if r.status_code != 200:
        print(f"  (accounts: user-service trả {r.status_code})"); return
    users = [u for u in r.json() if str(u.get("email", "")).endswith("@seed.local")]
    with open(f"{OUT}/accounts_seed.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "email", "full_name", "phone", "role"])
        for u in sorted(users, key=lambda x: x["email"]):
            w.writerow([u["id"], u["email"], u.get("full_name", ""), u.get("phone", ""), u["role"]])
    print(f"  accounts_seed.csv ({len(users)} tài khoản seed)")


if __name__ == "__main__":
    print("Xuất knowledge base →", OUT)
    export_behavior()
    try:
        export_graph()
    except Exception as e:
        print(f"  (graph lỗi: {e})")
    export_accounts()
    print("Xong.")
