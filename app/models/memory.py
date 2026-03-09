from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

from app.core.config import settings

# Ensure data directory exists
db_dir = os.path.dirname(settings.SQLITE_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.SQLITE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class MemoryDB(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    ai_name = Column(String, index=True, nullable=True)
    project = Column(String, index=True, nullable=True)
    title = Column(String, index=True)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True) # Stored as a JSON array
    category_main = Column(String, index=True, nullable=True)
    category_sub = Column(String, index=True, nullable=True)
    importance = Column(String, index=True, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    embedding_status = Column(String, default="pending")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
