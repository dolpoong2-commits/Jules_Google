from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
import logging

# --- Database Configuration ---
# Use a writable directory in /tmp for all runtime artifacts, including the database.
BASE_RUNTIME_PATH = "/tmp/solidworks_platform"
DB_DIR = os.path.join(BASE_RUNTIME_PATH, "db")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'jobs.db')}"

# The engine is the entry point to the database.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # Required for SQLite with FastAPI
)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our declarative models.
Base = declarative_base()


# --- SQLAlchemy Model for the 'jobs' table ---
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_uuid = Column(String, unique=True, index=True, nullable=False)
    task = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)

    # Store complex data like input/output details as JSON strings.
    input_payload = Column(Text, default="{}")
    result_payload = Column(Text, default="{}")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Job(id={self.id}, uuid='{self.job_uuid}', status='{self.status}')>"


# --- Utility to create the database and table ---
def init_db():
    """
    Creates the database tables if they don't exist.
    This should be called once on application startup.
    """
    logging.info(f"Initializing database at {DATABASE_URL}...")
    Base.metadata.create_all(bind=engine)
    logging.info("Database initialized.")