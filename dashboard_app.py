from flask import Flask, jsonify, render_template_string
import json
import os
import yaml

app = Flask(__name__)
STATE_FILE = "workflow_state.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Live Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }

        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h2 { color: #2980b9; margin-top: 0; display: flex; align-items: center; justify-content: space-between; }

        .status-badge { padding: 5px 12px; background: #34495e; color: white; border-radius: 20px; font-size: 0.9em; font-weight: normal; }
        .status-badge.active { background: #e67e22; animation: pulse 2s infinite; }
        .status-badge.complete { background: #27ae60; }
        .status-badge.error { background: #e74c3c; }

        .progress-container { width: 100%; background-color: #ecf0f1; border-radius: 8px; margin: 20px 0; overflow: hidden; height: 25px; }
        .progress-bar { height: 100%; background-color: #3498db; width: 0%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8em; font-weight: bold;}

        .metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e0e0e0; }
        .metric-title { font-size: 0.85em; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-size: 1.5em; color: #2c3e50; font-weight: bold; }

        .task-detail { background: #ecf0f1; padding: 15px; border-left: 4px solid #8e44ad; border-radius: 0 8px 8px 0; font-family: monospace; font-size: 1.1em; }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 OpenClaw Live Workflow Dashboard</h1>

        <div class="card">
            <h2>
                <span>Current Phase: <span id="phase">Waiting for tasks...</span></span>
                <span id="badge" class="status-badge">Idle</span>
            </h2>

            <div class="task-detail" id="status-detail">No active workflow.</div>

            <div class="progress-container">
                <div class="progress-bar" id="progress-bar">0%</div>
            </div>

            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-title">Tasks Completed</div>
                    <div class="metric-value" id="task-count">0 / 0</div>
                </div>
                <div class="metric">
                    <div class="metric-title">Elapsed Time</div>
                    <div class="metric-value" id="elapsed-time">0m 0s</div>
                </div>
                <div class="metric">
                    <div class="metric-title">Estimated Remaining</div>
                    <div class="metric-value" id="eta-time">-</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function formatTime(seconds) {
            if (!seconds && seconds !== 0) return "-";
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return `${m}m ${s}s`;
        }

        async function fetchState() {
            try {
                const response = await fetch('/api/state');
                if (!response.ok) return;
                const state = await response.json();

                document.getElementById('phase').innerText = state.phase || 'Idle';
                document.getElementById('status-detail').innerText = state.status || 'Waiting for tasks...';

                // Badge Logic
                const badge = document.getElementById('badge');
                if (state.phase === 'Complete') {
                    badge.className = 'status-badge complete';
                    badge.innerText = 'Finished';
                } else if (state.phase === 'Error') {
                    badge.className = 'status-badge error';
                    badge.innerText = 'Error';
                } else if (state.phase && state.phase !== 'Idle') {
                    badge.className = 'status-badge active';
                    badge.innerText = 'Running';
                }

                // Progress Bar
                const total = state.total_tasks || 0;
                const completed = state.completed_tasks || 0;
                let percent = 0;
                if (total > 0) percent = Math.round((completed / total) * 100);
                if (state.phase === 'Complete') percent = 100;

                const pb = document.getElementById('progress-bar');
                pb.style.width = percent + '%';
                pb.innerText = percent + '%';

                // Metrics
                document.getElementById('task-count').innerText = `${completed} / ${total}`;

                // Time calculations (using local clock to smoothly increment elapsed time between polls)
                if (state.start_time && state.phase !== 'Complete' && state.phase !== 'Error') {
                    const elapsed = (Date.now() / 1000) - state.start_time;
                    document.getElementById('elapsed-time').innerText = formatTime(elapsed);
                } else if (state.start_time && state.phase === 'Complete') {
                     // If complete, stop incrementing
                     const final_elapsed = state.timestamp - state.start_time;
                     document.getElementById('elapsed-time').innerText = formatTime(final_elapsed);
                }

                if (state.eta_seconds !== null) {
                    document.getElementById('eta-time').innerText = formatTime(state.eta_seconds);
                } else {
                    document.getElementById('eta-time').innerText = "Calculating...";
                }

            } catch (error) {
                console.error('Error fetching state:', error);
            }
        }

        // Poll every 1 second
        setInterval(fetchState, 1000);
        fetchState();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/state')
def get_state():
    if not os.path.exists(STATE_FILE):
        return jsonify({"phase": "Idle", "status": "Waiting for user command..."})

    try:
        with open(STATE_FILE, 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"phase": "Error", "status": f"Failed to read state: {e}"}), 500

if __name__ == '__main__':
    # Initialize empty state if not exists
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'w') as f:
            json.dump({"phase": "Idle", "status": "System Online. Waiting for Telegram commands."}, f)

    print("Starting Flask Live Dashboard on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)