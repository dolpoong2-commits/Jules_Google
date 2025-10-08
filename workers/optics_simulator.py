import sys
import os
from pathlib import Path
import datetime
import logging

# Basic logging setup for the worker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_optics_analysis(output_dir: str):
    """
    Simulates an optics analysis by creating a set of dummy output files
    (heatmap, csv report, pdf report) in the specified directory.
    """
    logging.info(f"--- Optics Simulator Worker ---")
    logging.info(f"Received request to generate outputs in: {output_dir}")

    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().isoformat()

        # 1. Create a dummy heatmap PNG
        heatmap_file = output_path / "heatmap.png"
        heatmap_content = f"Simulated heatmap image generated at {timestamp}"
        heatmap_file.write_text(heatmap_content, encoding="utf-8")
        logging.info(f"Successfully created dummy heatmap: {heatmap_file}")

        # 2. Create a dummy data CSV
        csv_file = output_path / "optics_data.csv"
        csv_content = "distance_mm,E_avg_lux,U0\n"
        csv_content += "50,550.1,0.71\n"
        csv_content += "100,412.3,0.62\n"
        csv_content += "200,250.8,0.55\n"
        csv_file.write_text(csv_content, encoding="utf-8")
        logging.info(f"Successfully created dummy CSV: {csv_file}")

        # 3. Create a dummy report PDF
        pdf_file = output_path / "optics_report.pdf"
        pdf_content = f"Simulated Optics Analysis Report\nGenerated at: {timestamp}"
        pdf_file.write_text(pdf_content, encoding="utf-8")
        logging.info(f"Successfully created dummy PDF report: {pdf_file}")

        # In a real script, stdout could return a JSON summary of created files.
        print(f"Success: Optics simulation complete. Files created in {output_dir}")

    except Exception as e:
        logging.error(f"An error occurred in the optics simulator: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing output directory path argument.", file=sys.stderr)
        print("Usage: python optics_simulator.py /path/to/output_directory", file=sys.stderr)
        sys.exit(1)

    output_dir_arg = sys.argv[1]
    simulate_optics_analysis(output_dir_arg)