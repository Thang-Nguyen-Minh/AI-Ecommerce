import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db, graph, vector_store
from .routers import admin, chatbot, events, recommend

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ecom-final ai-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, tags=["events"])
app.include_router(recommend.router, tags=["recommend"])
app.include_router(chatbot.router, tags=["chatbot"])
app.include_router(admin.router, tags=["admin"])


@app.on_event("startup")
def _startup():
    db.init_db()
    # Best-effort: nạp/dựng vector index trong nền (không chặn startup)
    import threading
    threading.Thread(target=vector_store.ensure_index, daemon=True).start()


@app.get("/health")
@app.get("/ai/health")
def health():
    return {
        "service": "ai-service",
        "status": "ok",
        "events": db.count_events(),
        "graph": graph.stats(),
        "vector": vector_store.stats(),
    }
