import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from qdrant_client.http.models import PointStruct

from app.models.schemas import MemoryCreate, MemoryResponse, MemoryUpdate, MemorySearchResponse
from app.models.memory import MemoryDB
from app.services.llm_service import generate_summary, auto_tag_and_categorize, generate_embedding, rerank_results
from app.core.qdrant_client import get_qdrant_client, COLLECTION_NAME

async def create_memory(db: Session, memory: MemoryCreate) -> MemoryResponse:
    # 1. Generate unique ID
    memory_id = f"conv_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"

    # 2. Extract metadata via LLM
    tagging_result = await auto_tag_and_categorize(memory.raw_text)

    # 3. Generate summary via LLM
    summary = await generate_summary(memory.raw_text)

    # 4. Determine title if not provided
    title = memory.title or summary[:50] + "..."

    # 5. Create DB Record (Metadata & Text)
    db_memory = MemoryDB(
        id=memory_id,
        ai_name=memory.ai_name,
        project=tagging_result.get("project") or memory.project,
        title=title,
        raw_text=memory.raw_text,
        summary=summary,
        tags=tagging_result.get("tags", []),
        category_main=tagging_result.get("category_main"),
        category_sub=tagging_result.get("category_sub"),
        importance=tagging_result.get("importance", "normal"),
        version=1,
        created_at=datetime.now(timezone.utc),
        embedding_status="pending"
    )

    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)

    # 6. Generate Embeddings & Save to Vector DB (Qdrant)
    # Combine text and summary for better semantic search
    content_to_embed = f"Title: {title}\nSummary: {summary}\nContent: {memory.raw_text}"
    embedding = await generate_embedding(content_to_embed)

    qdrant = get_qdrant_client()
    try:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload={
                        "title": title,
                        "project": db_memory.project,
                        "importance": db_memory.importance,
                        "tags": db_memory.tags,
                        "created_at": db_memory.created_at.isoformat()
                    }
                )
            ]
        )
        db_memory.embedding_status = "done"
        db.commit()
        db.refresh(db_memory)
    except Exception as e:
        print(f"Failed to upsert to Qdrant: {e}")
        db_memory.embedding_status = "failed"
        db.commit()

    return MemoryResponse.from_orm(db_memory)


async def search_memories(db: Session, query: str, limit: int = 5, min_score: float = 0.5) -> list[MemorySearchResponse]:
    qdrant = get_qdrant_client()

    # 1. Generate embedding for query
    query_vector = await generate_embedding(query)

    # 2. Semantic Search in Vector DB
    search_result = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit * 2,  # Fetch more for reranking
        score_threshold=min_score
    )

    results = []
    for hit in search_result:
        # 3. Retrieve full metadata from SQLite (to get latest summary/tags)
        memory = db.query(MemoryDB).filter(MemoryDB.id == hit.id).first()
        if memory:
            results.append({
                "id": memory.id,
                "title": memory.title,
                "summary": memory.summary,
                "tags": memory.tags,
                "project": memory.project,
                "importance": memory.importance,
                "created_at": memory.created_at,
                "score": hit.score
            })

    # 4. Rerank (Placeholder/Pass-through for now, until specific rerank endpoint is set up)
    reranked = await rerank_results(query, results)

    # Sort descending by score just in case, and limit
    reranked.sort(key=lambda x: x["score"], reverse=True)

    return [MemorySearchResponse(**res) for res in reranked[:limit]]


def update_memory_metadata(db: Session, memory_id: str, updates: MemoryUpdate) -> MemoryResponse:
    db_memory = db.query(MemoryDB).filter(MemoryDB.id == memory_id).first()
    if not db_memory:
        return None

    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_memory, key, value)

    # Increment version
    db_memory.version += 1

    db.commit()
    db.refresh(db_memory)

    # Update payload in Qdrant (tags, project, etc.)
    qdrant = get_qdrant_client()
    try:
        qdrant.set_payload(
            collection_name=COLLECTION_NAME,
            payload={
                "project": db_memory.project,
                "importance": db_memory.importance,
                "tags": db_memory.tags,
                "title": db_memory.title
            },
            points=[memory_id]
        )
    except Exception as e:
        print(f"Failed to update Qdrant payload: {e}")

    return MemoryResponse.from_orm(db_memory)

def get_memory(db: Session, memory_id: str) -> MemoryResponse:
    db_memory = db.query(MemoryDB).filter(MemoryDB.id == memory_id).first()
    if db_memory:
        return MemoryResponse.from_orm(db_memory)
    return None
