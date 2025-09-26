import os
import json
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def analyze_directory(directory_path: str) -> dict:
    """
    Performs a multi-faceted quality analysis on a given directory.

    Args:
        directory_path: The absolute path to the directory to analyze.

    Returns:
        A dictionary containing the analysis report.
    """
    report = {
        "pylint_findings": [],
        "license_findings": [],
        "secret_findings": [],
        "summary": {}
    }

    path_obj = Path(directory_path)
    if not path_obj.is_dir():
        logger.error(f"Directory not found: {directory_path}")
        return {"error": f"Directory not found: {directory_path}"}

    # --- 1. Pylint Analysis (for Python files) ---
    python_files = list(path_obj.rglob("*.py"))
    if python_files:
        logger.info(f"Running pylint on {len(python_files)} Python files...")
        try:
            pylint_cmd = ["pylint", "--output-format=json"] + [str(f) for f in python_files]
            # We run this with a timeout and check=False to handle cases where it might hang or fail
            result = subprocess.run(pylint_cmd, capture_output=True, text=True, timeout=120, check=False)
            if result.stdout:
                try:
                    report["pylint_findings"] = json.loads(result.stdout)
                except json.JSONDecodeError:
                    report["pylint_findings"] = {"error": "Failed to parse pylint JSON output.", "raw_output": result.stdout}
            if result.stderr:
                 logger.warning(f"Pylint stderr: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Pylint execution failed: {e}")
            report["pylint_findings"].append({"error": f"Pylint execution failed: {e}"})

    # --- 2. License Scanning (simple version) ---
    logger.info("Scanning for license files...")
    try:
        # A more robust solution would use spdx-tools, but for simplicity, we check for common license files.
        found_licenses = list(path_obj.glob("LICENSE*")) + list(path_obj.glob("COPYING*"))
        if found_licenses:
            for lic_path in found_licenses:
                report["license_findings"].append({"file": lic_path.name, "path": str(lic_path)})
        else:
            report["license_findings"].append({"message": "No common license file (LICENSE*, COPYING*) found in root."})
    except Exception as e:
        logger.error(f"License scan failed: {e}")
        report["license_findings"].append({"error": f"License scan failed: {e}"})

    # --- 3. TruffleHog Secret Scanning ---
    logger.info("Scanning for secrets with TruffleHog...")
    try:
        # Command: trufflehog filesystem /path/to/scan --json
        trufflehog_cmd = ["trufflehog", "filesystem", directory_path, "--json"]
        result = subprocess.run(trufflehog_cmd, capture_output=True, text=True, timeout=120, check=False)
        if result.stdout:
            # TruffleHog outputs JSON lines, so we parse each line
            secrets = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
            report["secret_findings"] = secrets
        if result.stderr:
            logger.warning(f"TruffleHog stderr: {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"TruffleHog execution failed: {e}")
        report["secret_findings"].append({"error": f"TruffleHog execution failed: {e}"})

    # --- 4. Generate Summary ---
    pylint_issue_count = len(report["pylint_findings"]) if isinstance(report["pylint_findings"], list) else 0
    report["summary"] = {
        "directories_scanned": 1,
        "python_files_found": len(python_files),
        "pylint_issues_found": pylint_issue_count,
        "secrets_found": len(report["secret_findings"]),
        "licenses_found": len(report["license_findings"]),
    }

    logger.info(f"Analysis complete for {directory_path}.")
    return report