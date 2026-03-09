import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LITELLM_BASE_URL: str = os.getenv("LITELLM_BASE_URL", "http://127.0.0.1:4000")
    LITELLM_API_KEY: str = os.getenv("LITELLM_API_KEY", "sk-david-local")
    LLM_MODEL_MAIN: str = os.getenv("LLM_MODEL_MAIN", "Qwen3-4B-Instruct-2507")
    LLM_MODEL_TAGGING: str = os.getenv("LLM_MODEL_TAGGING", "EXAONE 4.0 1.2B AWQ")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-0.6B")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1024")) # Typically 1024 for bge-m3 / modern models
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI bge-reranker-v2-m3")
    VECTOR_DB: str = os.getenv("VECTOR_DB", "qdrant")
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./data/qdrant")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./data/memory.db")

settings = Settings()
