import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

# Ensure data directory exists
if settings.QDRANT_PATH and not os.path.exists(settings.QDRANT_PATH):
    os.makedirs(settings.QDRANT_PATH, exist_ok=True)

# Initialize Qdrant Client using local path
qdrant = QdrantClient(path=settings.QDRANT_PATH)

COLLECTION_NAME = "memories"
VECTOR_SIZE = settings.EMBEDDING_DIM

# Create collection if it doesn't exist
try:
    qdrant.get_collection(collection_name=COLLECTION_NAME)
except Exception:
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
    )

def get_qdrant_client() -> QdrantClient:
    return qdrant
