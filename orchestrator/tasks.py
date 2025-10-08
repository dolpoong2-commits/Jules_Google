import subprocess
import sys
import json
from pathlib import Path
import platform
import datetime
import logging
import os

from .celery_config import celery_app
from .database import SessionLocal, Job

# Define a single, writable base path for all runtime artifacts
BASE_RUNTIME_PATH = Path("/tmp/solidworks_platform")

@celery_app.task(bind=True)
def run_conversion_task(self, job_uuid: str):
    """
    A Celery task that executes the conversion worker subprocess.
    """
    logging.info(f"Celery conversion task started for job_uuid: {job_uuid}")
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_uuid == job_uuid).first()
    if not job:
        logging.error(f"Job with UUID {job_uuid} not found in the database.")
        db.close()
        return "FAILURE"

    return_status = "error"
    try:
        job.status = "running"
        db.commit()

        job_ticket_for_worker = {"job_id": job.job_uuid, "input": json.loads(job.input_payload)}
        temp_dir = BASE_RUNTIME_PATH / "temp"
        temp_dir.mkdir(exist_ok=True)
        job_ticket_path = temp_dir / f"{job.job_uuid}.json"
        with open(job_ticket_path, 'w') as f:
            json.dump(job_ticket_for_worker, f, indent=2)

        worker_type = "simulator"
        if platform.system() == "Windows":
            worker_type = "C# (real)"
            worker_exe = Path(__file__).resolve().parent.parent / "workers" / "converter-csharp" / "bin" / "Release" / "SolidworksConverter.exe"
            command = [str(worker_exe), str(job_ticket_path)]
        else:
            worker_type = "Python (simulator)"
            worker_script = Path(__file__).resolve().parent.parent / "workers" / "converter_simulator.py"
            command = [sys.executable, str(worker_script), str(job_ticket_path)]

        logging.info(f"Executing command on {platform.system()} using {worker_type} worker: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            job.status = "success"
            job.result_payload = json.dumps({"output_path": result.stdout.strip(), "worker": worker_type})
        else:
            job.status = "failure"
            job.result_payload = json.dumps({"error": result.stderr.strip(), "worker": worker_type})
        db.commit()

    except Exception as e:
        db.rollback()
        job.status = "failure"
        job.result_payload = json.dumps({"error": f"An unexpected error in Celery task: {str(e)}"})
        db.commit()
        logging.exception(f"Celery task failed for job {job_uuid}")
        raise
    finally:
        return_status = job.status
        db.close()
    return return_status


@celery_app.task(bind=True)
def run_rendering_task(self, job_uuid: str):
    """
    A Celery task that executes the REAL Blender rendering worker with a specific profile.
    This will fail in environments where 'blender' is not in the PATH.
    """
    logging.info(f"Celery rendering task started for job_uuid: {job_uuid}")
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_uuid == job_uuid).first()
    if not job:
        logging.error(f"Job with UUID {job_uuid} not found for rendering.")
        db.close()
        return "FAILURE"

    return_status = "error"
    try:
        job.status = "running"
        db.commit()
        logging.info(f"Rendering job {job_uuid} status updated to 'running'.")

        input_data = json.loads(job.input_payload)
        input_obj_path = Path(input_data['files'][0])
        render_profile_name = input_data.get("profiles", {}).get("render", "standard")
        profile_path = Path(__file__).resolve().parent.parent / "profiles" / "render" / f"{render_profile_name}.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Render profile '{render_profile_name}.json' not found.")

        with open(profile_path, 'r') as f:
            render_profile = json.load(f)

        output_root = BASE_RUNTIME_PATH / "Output"
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir_name = f"{input_obj_path.stem}_{timestamp}"
        render_output_dir = output_root / output_dir_name / "render"
        render_output_dir.mkdir(parents=True, exist_ok=True)

        output_file_path = render_output_dir / f"{input_obj_path.stem}_{render_profile_name}.png"
        worker_script = Path(__file__).resolve().parent.parent / "workers" / "renderer_blender.py"
        profile_json_string = json.dumps(render_profile)

        command = [
            "blender", "--background", "--python", str(worker_script),
            "--", str(input_obj_path), str(output_file_path), profile_json_string
        ]

        logging.info(f"Executing REAL Blender command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            job.status = "success"
            job.result_payload = json.dumps({"output_path": str(output_file_path), "profile_used": render_profile})
        else:
            job.status = "failure"
            job.result_payload = json.dumps({"error": result.stderr.strip() or f"Blender execution failed with code {result.returncode}"})
        db.commit()
        logging.info(f"Rendering job {job_uuid} completed with status: {job.status}.")

    except Exception as e:
        db.rollback()
        job.status = "failure"
        job.result_payload = json.dumps({"error": f"An unexpected error occurred in rendering task: {str(e)}"})
        db.commit()
        logging.exception(f"Rendering task failed for job {job_uuid}")
        raise
    finally:
        return_status = job.status
        db.close()
    return return_status

@celery_app.task(bind=True)
def run_optics_task(self, job_uuid: str):
    """
    A Celery task that executes the optics simulation worker.
    """
    logging.info(f"Celery optics simulation task started for job_uuid: {job_uuid}")
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_uuid == job_uuid).first()
    if not job:
        logging.error(f"Job with UUID {job_uuid} not found for optics simulation.")
        db.close()
        return "FAILURE"

    return_status = "error"
    try:
        job.status = "running"
        db.commit()
        logging.info(f"Optics job {job_uuid} status updated to 'running'.")

        input_data = json.loads(job.input_payload)
        # The input for this task is the output of the conversion task
        input_obj_path = Path(input_data['files'][0])

        output_root = BASE_RUNTIME_PATH / "Output"
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir_name = f"{input_obj_path.stem}_{timestamp}"
        optics_output_dir = output_root / output_dir_name / "optics"
        optics_output_dir.mkdir(parents=True, exist_ok=True)

        worker_script = Path(__file__).resolve().parent.parent / "workers" / "optics_simulator.py"
        command = [sys.executable, str(worker_script), str(optics_output_dir)]

        logging.info(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            job.status = "success"
            job.result_payload = json.dumps({
                "output_directory": str(optics_output_dir),
                "files_generated": ["heatmap.png", "optics_data.csv", "optics_report.pdf"]
            })
        else:
            job.status = "failure"
            job.result_payload = json.dumps({"error": result.stderr.strip()})
        db.commit()
        logging.info(f"Optics job {job_uuid} completed with status: {job.status}.")

    except Exception as e:
        db.rollback()
        job.status = "failure"
        job.result_payload = json.dumps({"error": f"An unexpected error occurred in the optics task: {str(e)}"})
        db.commit()
        logging.exception(f"Optics task failed for job {job_uuid}")
        raise
    finally:
        return_status = job.status
        db.close()

    return return_status