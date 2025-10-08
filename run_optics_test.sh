#!/bin/bash

# A script to run a controlled, end-to-end test of the convert -> optics pipeline.

echo "--- Optics Pipeline Test: Starting ---"
set -e # Exit immediately if a command exits with a non-zero status.

# 1. Clean up & Setup
echo "[1/7] Initializing environment..."
pkill -f uvicorn || true # Ignore error if no process is found
LOG_DIR="/tmp/solidworks_platform/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/orchestrator.log"
rm -f "$LOG_FILE" # Clear old log

# 2. Start Server
echo "[2/7] Starting Uvicorn server in the background..."
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &
UVICORN_PID=$!
echo "Server started with PID: $UVICORN_PID"
sleep 5 # Wait for boot

# 3. Request Conversion
echo "[3/7] Requesting STEP conversion to generate OBJ file..."
CONVERT_RESPONSE=$(curl -s -X POST "http://localhost:8000/jobs/convert" \
-H "Content-Type: application/json" \
-d '{
  "files": ["C:/models/my_optical_component.SLDPRT"],
  "profiles": { "step": "fast_preview" },
  "output_root": "/tmp/solidworks_platform/Output"
}')
CONVERT_JOB_ID=$(echo $CONVERT_RESPONSE | jq -r .job_id)
echo "Conversion job created with ID: $CONVERT_JOB_ID"

# 4. Poll for Conversion Result
echo "[4/7] Polling for conversion result..."
OBJ_FILE_PATH=""
for i in {1..5}; do
    STATUS_RESPONSE=$(curl -s "http://localhost:8000/jobs/$CONVERT_JOB_ID")
    JOB_STATUS=$(echo $STATUS_RESPONSE | jq -r .status)
    echo "  - Poll $i: Status is $JOB_STATUS"
    if [ "$JOB_STATUS" == "success" ]; then
        OBJ_FILE_PATH=$(echo $STATUS_RESPONSE | jq -r .details.output_path)
        echo "  - Success! OBJ file created at: $OBJ_FILE_PATH"
        break
    fi
    sleep 2
done

if [ -z "$OBJ_FILE_PATH" ]; then
    echo "Error: Conversion did not succeed in time."
    kill $UVICORN_PID
    exit 1
fi

# 5. Request Optics Analysis
echo "[5/7] Requesting optics analysis using the generated OBJ file..."
OPTICS_RESPONSE=$(curl -s -X POST "http://localhost:8000/jobs/optics" \
-H "Content-Type: application/json" \
-d "{
  \"files\": [\"$OBJ_FILE_PATH\"],
  \"profiles\": { \"optics\": \"accurate\" },
  \"output_root\": \"/tmp/solidworks_platform/Output\"
}")
OPTICS_JOB_ID=$(echo $OPTICS_RESPONSE | jq -r .job_id)
echo "Optics job created with ID: $OPTICS_JOB_ID"

# 6. Verify Optics Result
echo "[6/7] Verifying optics analysis results..."
sleep 2 # Give it a moment to run
OPTICS_STATUS_RESPONSE=$(curl -s "http://localhost:8000/jobs/$OPTICS_JOB_ID")
OPTICS_JOB_STATUS=$(echo $OPTICS_STATUS_RESPONSE | jq -r .status)
if [ "$OPTICS_JOB_STATUS" == "success" ]; then
    OUTPUT_DIR=$(echo $OPTICS_STATUS_RESPONSE | jq -r .details.output_directory)
    echo "  - Success! Verifying files in $OUTPUT_DIR..."
    ls -l "$OUTPUT_DIR"
else
    echo "Error: Optics job failed with status $OPTICS_JOB_STATUS"
    cat "$LOG_FILE"
    kill $UVICORN_PID
    exit 1
fi

# 7. Clean up
echo "[7/7] Killing server process with PID: $UVICORN_PID"
kill $UVICORN_PID
echo "--- Optics Pipeline Test: Finished Successfully! ---"