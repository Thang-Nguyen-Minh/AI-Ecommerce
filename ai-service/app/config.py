import os

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-default-secret-key")
JWT_ALGORITHM = "HS256"

PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://localhost:8002")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "ecom123")

# Behavior store (SQLite) — DB riêng của ai-service, persist qua volume mount
BEHAVIOR_DB = os.environ.get("BEHAVIOR_DB", "/app/ai_data/behavior.db")

# RAG vector store (FAISS) + LSTM snapshot — runtime data (gitignored)
VECTOR_DIR = os.environ.get("VECTOR_DIR", "/app/ai_data/vector")
LSTM_DIR = os.environ.get("LSTM_DIR", "/app/ai_data/lstm")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

# Trọng số hybrid (GĐ5): final = w1·lstm + w2·graph + w3·popularity
W_LSTM = float(os.environ.get("W_LSTM", "0.2"))
W_GRAPH = float(os.environ.get("W_GRAPH", "0.5"))
W_POP = float(os.environ.get("W_POP", "0.3"))

VALID_ACTIONS = {"view", "click", "add_to_cart"}
