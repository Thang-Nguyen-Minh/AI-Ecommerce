from fastapi import APIRouter, Depends, HTTPException

from .. import db, graph, vector_store
from ..auth import CurrentUser, get_current_user

router = APIRouter()


@router.post("/admin/build-graph")
def build_graph(threshold: int = 5, user: CurrentUser = Depends(get_current_user)):
    """
    GĐ3: dựng lại cạnh VIEW/BUY từ behavior store + tính SIMILAR.
    Chỉ admin/staff. Dùng sau khi seed (batch) hoặc khi muốn refresh graph.
    """
    if user.role not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Chỉ admin/staff")
    if not graph.available():
        raise HTTPException(status_code=503, detail="Neo4j không khả dụng")

    ok_edges = graph.rebuild_from_events(db.all_events())
    ok_sim = graph.compute_similar(threshold=threshold)
    return {
        "rebuilt": ok_edges,
        "similar_computed": ok_sim,
        "threshold": threshold,
        "stats": graph.stats(),
    }


@router.post("/admin/build-vector")
def build_vector(user: CurrentUser = Depends(get_current_user)):
    """GĐ4: dựng FAISS index từ catalog product-service (RAG)."""
    if user.role not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Chỉ admin/staff")
    count = vector_store.build_index()
    return {"indexed": count, "stats": vector_store.stats()}
