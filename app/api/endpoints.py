from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.models.schemas import MemoryCreate, MemoryResponse, MemoryUpdate, MemorySearchResponse
from app.models.memory import get_db
from app.services.memory_service import create_memory, search_memories, update_memory_metadata, get_memory

router = APIRouter()

@router.post("/", response_model=MemoryResponse)
async def create_new_memory(memory: MemoryCreate, db: Session = Depends(get_db)):
    try:
        new_memory = await create_memory(db, memory)
        return new_memory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[MemorySearchResponse])
async def search_memory_store(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=50),
    min_score: float = Query(0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    try:
        results = await search_memories(db, query, limit, min_score)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory_by_id(memory_id: str, db: Session = Depends(get_db)):
    memory = get_memory(db, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory_metadata_by_id(memory_id: str, updates: MemoryUpdate, db: Session = Depends(get_db)):
    updated_memory = update_memory_metadata(db, memory_id, updates)
    if not updated_memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return updated_memory
