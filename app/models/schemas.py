from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MemoryBase(BaseModel):
    title: str
    raw_text: str
    ai_name: Optional[str] = "System"
    project: Optional[str] = None

class MemoryCreate(MemoryBase):
    pass

class MemoryUpdate(BaseModel):
    tags: Optional[List[str]] = None
    category_main: Optional[str] = None
    category_sub: Optional[str] = None
    importance: Optional[str] = None
    project: Optional[str] = None
    title: Optional[str] = None

class MemoryResponse(MemoryBase):
    id: str
    summary: Optional[str] = None
    tags: List[str] = []
    category_main: Optional[str] = None
    category_sub: Optional[str] = None
    importance: Optional[str] = None
    version: int
    created_at: datetime
    embedding_status: str

    class Config:
        from_attributes = True

class MemorySearchResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    tags: List[str] = []
    project: Optional[str] = None
    importance: Optional[str] = None
    created_at: datetime
    score: float

class TaggingResponse(BaseModel):
    summary: str
    tags: List[str]
    category_main: str
    category_sub: str
    importance: str # low, normal, high, critical
    project: str
