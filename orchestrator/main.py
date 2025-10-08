# --- 1. Logging Bootstrap ---
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Use a writable directory in /tmp for all runtime artifacts
BASE_RUNTIME_PATH = "/tmp/solidworks_platform"

LOG_DIR = os.path.join(BASE_RUNTIME_PATH, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, "orchestrator.log")

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

if not root_logger.handlers:
    fh = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    root_logger.addHandler(fh)
    root_logger.addHandler(sh)

logging.info(">>> Logger initialized. Log path: %s", log_path)


# --- 2. Standard Imports ---
import json
from uuid import uuid4
import traceback

# Add project root to sys.path AFTER logging is configured
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# --- 3. Local Application Imports ---
from orchestrator.models import JobInput, JobStatusResponse
from orchestrator.database import SessionLocal, init_db, Job
from orchestrator.tasks import run_conversion_task, run_rendering_task, run_optics_task
from orchestrator.celery_config import celery_app

# --- 4. FastAPI App Initialization ---
app = FastAPI(
    title="SolidWorks All-in-One Platform Orchestrator",
    description="API for managing conversion, rendering, and optics simulation jobs.",
    version="1.4 (Fixed Paths)"
)

# --- Middleware & Exception Handlers ---
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    logging.info(f"REQ {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"RES {response.status_code} {request.url}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})

# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI Events ---
@app.on_event("startup")
def on_startup():
    logging.info("--- Application starting up... ---")
    init_db()

# --- API Endpoints ---
@app.post("/jobs/convert", response_model=JobStatusResponse, status_code=202, tags=["Jobs"])
def create_convert_job(job_input: JobInput, db: Session = Depends(get_db)):
    job_uuid = str(uuid4())
    new_job = Job(job_uuid=job_uuid, task="convert", status="queued", input_payload=job_input.json())
    db.add(new_job)
    db.commit()
    logging.info(f"Job {job_uuid} (convert) created and saved to DB.")
    run_conversion_task.delay(job_uuid)
    return JobStatusResponse(job_id=job_uuid, task="convert", status="queued")

@app.post("/jobs/render", response_model=JobStatusResponse, status_code=202, tags=["Jobs"])
def create_render_job(job_input: JobInput, db: Session = Depends(get_db)):
    job_uuid = str(uuid4())
    new_job = Job(job_uuid=job_uuid, task="render", status="queued", input_payload=job_input.json())
    db.add(new_job)
    db.commit()
    logging.info(f"Job {job_uuid} (render) created and saved to DB.")
    run_rendering_task.delay(job_uuid)
    return JobStatusResponse(job_id=job_uuid, task="render", status="queued")

@app.post("/jobs/optics", response_model=JobStatusResponse, status_code=202, tags=["Jobs"])
def create_optics_job(job_input: JobInput, db: Session = Depends(get_db)):
    """
    Receives an optics simulation job request and dispatches it to Celery.
    """
    job_uuid = str(uuid4())
    new_job = Job(job_uuid=job_uuid, task="optics", status="queued", input_payload=job_input.json())
    db.add(new_job)
    db.commit()
    logging.info(f"Job {job_uuid} (optics) created and saved to DB.")
    run_optics_task.delay(job_uuid)
    logging.info(f"Celery task for job {job_uuid} (optics) dispatched.")
    return JobStatusResponse(job_id=job_uuid, task="optics", status="queued")

@app.get("/jobs/{job_uuid}", response_model=JobStatusResponse, tags=["Jobs"])
def get_job_status(job_uuid: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_uuid == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    details = {}
    if job.status in ["success", "failure"]:
        try:
            details = json.loads(job.result_payload)
        except (json.JSONDecodeError, TypeError):
            details = {"payload": job.result_payload}
    return JobStatusResponse(job_id=job.job_uuid, task=job.task, status=job.status, details=details)

# --- Health Check Endpoints ---
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@app.get("/health/redis", tags=["Health"])
def health_check_redis():
    try:
        celery_app.broker_connection().ensure_connection(max_retries=1)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {str(e)}")

@app.get("/health/celery", tags=["Health"])
def health_check_celery():
    try:
        response = celery_app.control.ping(timeout=2.0)
        if not response:
            raise HTTPException(status_code=503, detail="No active Celery workers found.")
        return {"status": "ok", "workers": response}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Celery ping failed: {str(e)}")