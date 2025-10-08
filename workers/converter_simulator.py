import sys
import json
from pathlib import Path
import datetime
import logging

# Basic logging setup for the worker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_conversion_to_obj(job_ticket_path: Path):
    """
    Reads a job ticket JSON and simulates the conversion process
    by creating a syntactically correct, dummy .obj file (a simple cube).
    """
    logging.info(f"--- Python Converter Simulator (to OBJ) ---")
    logging.info(f"Reading job ticket from: {job_ticket_path}")

    if not job_ticket_path.exists():
        logging.error(f"Error: Job ticket not found at {job_ticket_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(job_ticket_path, 'r') as f:
            job = json.load(f)

        input_file_path = Path(job['input']['files'][0])
        output_root = Path(job['input']['output_root'])

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir_name = f"{input_file_path.stem}_{timestamp}"
        # The output is now a generic "conversion" directory, not "step"
        conversion_output_dir = output_root / output_dir_name / "conversion"

        conversion_output_dir.mkdir(parents=True, exist_ok=True)

        # The output file is now an .obj file
        output_file_path = conversion_output_dir / f"{input_file_path.stem}.obj"

        logging.info(f"Simulating OBJ conversion for: {input_file_path}")
        logging.info(f"Output target: {output_file_path}")

        # A simple cube definition in OBJ format
        obj_content = """
# Simple Cube
v 1.0 1.0 -1.0
v 1.0 -1.0 -1.0
v 1.0 1.0 1.0
v 1.0 -1.0 1.0
v -1.0 1.0 -1.0
v -1.0 -1.0 -1.0
v -1.0 1.0 1.0
v -1.0 -1.0 1.0
f 1 3 4 2
f 5 7 8 6
f 1 5 7 3
f 2 6 8 4
f 3 7 8 4
f 1 2 6 5
"""
        output_file_path.write_text(obj_content.strip())

        # The worker's output (stdout) should be the path to the created file.
        # This is crucial for the next step in the pipeline.
        print(str(output_file_path))
        logging.info(f"--- Simulation successful. OBJ file created at: {output_file_path} ---")
        sys.exit(0)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python converter_simulator.py <path_to_job_ticket.json>", file=sys.stderr)
        sys.exit(1)

    job_ticket_file = Path(sys.argv[1])
    simulate_conversion_to_obj(job_ticket_file)