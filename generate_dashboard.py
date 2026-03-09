import yaml
import json

def generate_html_dashboard():
    # Load Docker config
    with open('docker-compose.models.yml', 'r') as f:
        docker_conf = yaml.safe_load(f)

    # Load LiteLLM config
    with open('litellm_config.yaml', 'r') as f:
        litellm_conf = yaml.safe_load(f)

    # Load MCP config
    with open('mcp_config.json', 'r') as f:
        mcp_conf = json.load(f)

    # Parse GPU allocations
    gpu0_models = []
    gpu1_models = []

    for svc_name, details in docker_conf.get('services', {}).items():
        env_vars = details.get('environment', [])
        is_gpu0 = any("CUDA_VISIBLE_DEVICES=0" in env for env in env_vars)

        command = details.get('command', '')
        model_name = "Unknown"
        vram_util = "Unknown"

        for part in command.split():
            if "EXAONE" in part or "Llama" in part or "Qwen" in part:
                model_name = part.replace('"', '').split('/')[-1]
            if part.startswith("0."):
                vram_util = f"{float(part)*100}%"

        info = {
            "name": svc_name,
            "model": model_name,
            "port": details.get('ports', ['Unknown'])[0].split(':')[0],
            "vram_util": vram_util
        }

        if is_gpu0:
            gpu0_models.append(info)
        else:
            gpu1_models.append(info)

    # Parse MCP Tools
    mcp_tools = list(mcp_conf.get('mcpServers', {}).keys())

    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Local LLM Multi-Agent System Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h2 {{ color: #2980b9; margin-top: 0; }}
            .gpu-card {{ border-left: 5px solid #e74c3c; }}
            .gpu-card.gpu1 {{ border-left-color: #27ae60; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; }}
            .badge {{ display: inline-block; padding: 5px 10px; background: #34495e; color: white; border-radius: 15px; font-size: 0.85em; margin: 2px; }}
            .flow-box {{ background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #8e44ad; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Local LLM Multi-Agent Dashboard</h1>

            <div class="grid">
                <!-- GPU 0 -->
                <div class="card gpu-card">
                    <h2>🖥️ GPU 0 (RTX 3090 - 24GB)</h2>
                    <p><strong>Role:</strong> Heavy Inference (Planning, QA, Structuring)</p>
                    <table>
                        <tr><th>Container</th><th>Model</th><th>Port</th><th>VRAM Limit</th></tr>
                        {"".join([f"<tr><td>{m['name']}</td><td>{m['model']}</td><td>{m['port']}</td><td>{m['vram_util']}</td></tr>" for m in gpu0_models])}
                    </table>
                </div>

                <!-- GPU 1 -->
                <div class="card gpu-card gpu1">
                    <h2>🖥️ GPU 1 (RTX 5060ti - 16GB)</h2>
                    <p><strong>Role:</strong> Concurrent Worker Fleet (Execution, Tool Use)</p>
                    <table>
                        <tr><th>Container</th><th>Model</th><th>Port</th><th>VRAM Limit</th></tr>
                        {"".join([f"<tr><td>{m['name']}</td><td>{m['model']}</td><td>{m['port']}</td><td>{m['vram_util']}</td></tr>" for m in gpu1_models])}
                    </table>
                </div>

                <!-- 5-Tier Workflow -->
                <div class="card">
                    <h2>⚙️ 5-Tier Planner Workflow</h2>
                    <div class="flow-box"><strong>Tier 1. OpenClaw:</strong> Telegram Command Reception</div>
                    <div class="flow-box"><strong>Tier 2. AntiGravity:</strong> Architecture & Tech Stack Planning (GPU 0)</div>
                    <div class="flow-box"><strong>Tier 3. OpenGoat:</strong> Role Delegation & Task Breakdown (GPU 0)</div>
                    <div class="flow-box"><strong>Tier 4. Cursor:</strong> 6-Step Implementation Loop (GPU 1)</div>
                    <div class="flow-box"><strong>Tier 5. MCP:</strong> Sandbox Tool Access</div>
                    <div class="flow-box"><strong>Tier 6. QA Consistency:</strong> Validation against Tier 2 Plan (GPU 0)</div>
                </div>

                <!-- MCP Tools -->
                <div class="card">
                    <h2>🛠️ Connected MCP Tools</h2>
                    <p>The Cursor implementation tier automatically injects the following tools into the OpenClaw agent:</p>
                    <div>
                        {"".join([f'<span class="badge">{tool}</span>' for tool in mcp_tools])}
                    </div>
                    <h3 style="margin-top:20px; color:#2c3e50;">LiteLLM Proxy Endpoints</h3>
                    <p><strong>Planner Alias:</strong> <code>openai/planner-model</code></p>
                    <p><strong>Worker Aliases:</strong> <code>openai/worker-exaone-1.2b</code> (x5)</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    with open('dashboard.html', 'w') as f:
        f.write(html_content)
    print("dashboard.html successfully generated.")

if __name__ == "__main__":
    generate_html_dashboard()