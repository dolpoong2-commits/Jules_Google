#!/bin/bash

# A script to run a controlled, end-to-end test of the orchestrator.

echo "--- Test Run: Starting ---"

# 1. Clean up any previous processes to ensure a clean slate.
echo "[1/6] Killing previous uvicorn processes..."
pkill -f uvicorn
sleep 1

# 2. Start the orchestrator server in the background.
LOG_FILE="/tmp/solidworks_platform/logs/orchestrator.log"
echo "[2/6] Starting Uvicorn server in the background..."
# Ensure log directory exists
mkdir -p /tmp/solidworks_platform/logs
uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &
UVICORN_PID=$!
echo "Server started with PID: $UVICORN_PID"

# 3. Wait for the server to initialize.
echo "[3/6] Waiting 5 seconds for the server to boot..."
sleep 5

# 4. Send a curl request to test the /jobs/render endpoint.
echo "[4/6] Sending curl request with 'draft' profile..."
curl -X POST "http://localhost:8000/jobs/render" \
-H "Content-Type: application/json" \
-d '{
  "files": ["/path/to/dummy_input.step"],
  "profiles": { "render": "draft" },
  "output_root": "/tmp/solidworks_platform/Output"
}'
echo -e "\nCurl request finished."

# 5. Display the logs to see what happened.
echo "[5/6] Displaying contents of the log file at $LOG_FILE:"
sleep 2 # Wait a moment for logs from the curl request to be written.
if [ -f "$LOG_FILE" ]; then
    cat "$LOG_FILE"
else
    echo "Log file not found!"
fi

# 6. Clean up the server process.
echo "[6/6] Killing server process with PID: $UVICORN_PID"
kill $UVICORN_PID

echo "--- Test Run: Finished ---"