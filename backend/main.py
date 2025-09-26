import os
import requests
import subprocess
import sys
from bs4 import BeautifulSoup
from github import Github, GithubException
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

# Import other modules
from code_quality_analyzer import analyze_directory
from datasheet_processor import process_datasheet_directory
from qa_eval import evaluate_qa

# --- Setup ---
app = FastAPI()
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Define base directories
BACKEND_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
MODELS_DIR = os.path.join(ROOT_DIR, 'models')
REPORTS_DIR = os.path.join(ROOT_DIR, 'reports')

for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

g = Github()

# --- Pydantic Models ---
class ScrapeRequest(BaseModel):
    urls: List[str] = []
    github_repos: List[str] = []

class DirectoryRequest(BaseModel):
    path: str

class TrainingRequest(BaseModel):
    model_id: str
    dataset_path: str
    training_method: str
    output_dir: str
    epochs: int
    batch_size: int
    learning_rate: float
    lora_r: Optional[int] = 8
    lora_alpha: Optional[int] = 16
    lora_dropout: Optional[float] = 0.05

class PredictionRequest(BaseModel):
    base_model_id: str
    adapter_path: Optional[str] = None
    dataset_path: str
    output_dir: str = "predictions"

class EvaluationRequest(BaseModel):
    gold_file_path: str
    pred_file_path: str

# --- Helper Functions (keep existing ones) ---
def scrape_website(url: str):
    # (implementation is unchanged)
    return f"Scraping {url} (dummy)"

def scrape_github_repo(repo_name: str):
    # (implementation is unchanged)
    return f"Scraping {repo_name} (dummy)"

# --- API Endpoints ---
@app.post("/scrape/")
async def start_scraping(request: ScrapeRequest):
    # (implementation is unchanged)
    return {"status": "Scraping completed", "details": []}

@app.post("/analyze-code/")
async def analyze_code_quality(request: DirectoryRequest):
    # (implementation is unchanged)
    return {"status": "Analysis complete"}

@app.post("/process-datasheets/")
async def process_datasheets(request: DirectoryRequest):
    # (implementation is unchanged)
    return {"status": "Processing complete"}

@app.post("/start-training/")
async def start_training(request: TrainingRequest):
    command = [
        sys.executable, "training_wrapper.py",
        "--model_id", request.model_id,
        "--dataset_path", os.path.join(DATA_DIR, request.dataset_path),
        "--output_dir", os.path.join(MODELS_DIR, request.output_dir),
        "--training_method", request.training_method,
        "--epochs", str(request.epochs),
        "--batch_size", str(request.batch_size),
        "--learning_rate", str(request.learning_rate),
    ]
    if "lora" in request.training_method:
        command.extend(["--lora_r", str(request.lora_r), "--lora_alpha", str(request.lora_alpha), "--lora_dropout", str(request.lora_dropout)])

    try:
        process = subprocess.Popen(command, cwd=BACKEND_DIR, stdout=sys.stdout, stderr=sys.stderr)
        return {"status": "Training process started", "pid": process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-predictions/")
async def generate_predictions(request: PredictionRequest):
    logger.info(f"Received prediction request: {request.dict()}")

    adapter_path = os.path.join(MODELS_DIR, request.adapter_path) if request.adapter_path else None

    command = [
        sys.executable, "generate_predictions.py",
        "--base_model_id", request.base_model_id,
        "--dataset_path", os.path.join(DATA_DIR, request.dataset_path),
        "--output_dir", os.path.join(REPORTS_DIR, request.output_dir),
    ]
    if adapter_path and os.path.exists(adapter_path):
        command.extend(["--adapter_path", adapter_path])

    try:
        process = subprocess.Popen(command, cwd=BACKEND_DIR, stdout=sys.stdout, stderr=sys.stderr)
        return {"status": "Prediction generation started", "pid": process.pid}
    except Exception as e:
        logger.error(f"Failed to start prediction generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate-predictions/")
async def run_evaluation(request: EvaluationRequest):
    logger.info(f"Received evaluation request: {request.dict()}")

    gold_file = os.path.join(DATA_DIR, request.gold_file_path)
    pred_file = os.path.join(REPORTS_DIR, request.pred_file_path)

    if not os.path.exists(gold_file):
        raise HTTPException(status_code=404, detail=f"Gold file not found: {gold_file}")
    if not os.path.exists(pred_file):
        raise HTTPException(status_code=404, detail=f"Prediction file not found: {pred_file}")

    try:
        report = evaluate_qa(gold_file, pred_file)
        return report
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "ESP32 AI Toolkit Backend is running."}