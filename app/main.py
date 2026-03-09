from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as memory_router
from app.core.config import settings

app = FastAPI(
    title="AI Memory System API",
    description="AI 대화 기억 시스템 + 의미 검색 + 자동 분류 시스템",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router, prefix="/api/memory", tags=["Memory"])

@app.get("/")
def read_root():
    return {"message": "AI Memory System API is running."}
