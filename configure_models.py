#!/usr/bin/env python3
import yaml
import sys

def prompt_choice(prompt, options):
    print(f"\n{prompt}")
    for idx, opt in enumerate(options, 1):
        print(f"  {idx}. {opt['name']} ({opt['desc']})")

    while True:
        try:
            choice = int(input("Select an option number: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        print("Invalid choice, please try again.")

def main():
    print("=== Local LLM Inference Configurator ===")

    # Define available Heavy Models (GPU 0 - RTX 3090 24GB)
    heavy_models = [
        {"id": "exaone-32b-awq", "name": "Exaone 32B (4-bit AWQ)", "repo": "LGAI-EXAONE/EXAONE-3.0-32B-Instruct-AWQ", "desc": "Requires AWQ quantization", "quant": "awq", "max_len": 4096},
        {"id": "gpt-oss-20b", "name": "GPT-OSS 20B", "repo": "gpt-oss-repo/20b-instruct", "desc": "Native FP16, fits in 24GB", "quant": None, "max_len": 4096},
        {"id": "qwen2.5-32b-awq", "name": "Qwen 2.5 32B (4-bit AWQ)", "repo": "Qwen/Qwen2.5-32B-Instruct-AWQ", "desc": "Alternative 32B", "quant": "awq", "max_len": 8192},
        {"id": "custom", "name": "Custom Model", "repo": "", "desc": "Enter your own HuggingFace Repo ID", "quant": None, "max_len": 4096}
    ]

    # Define available Light Models (GPU 1 - RTX 5060ti 16GB)
    light_models = [
        {"id": "exaone-1.2b", "name": "Exaone 1.2B", "repo": "LGAI-EXAONE/EXAONE-1.2B", "desc": "Very fast, small footprint", "vram_est": 3},
        {"id": "llama3.2-3b", "name": "Llama 3.2 3B", "repo": "meta-llama/Llama-3.2-3B-Instruct", "desc": "Great logic for its size", "vram_est": 7},
        {"id": "qwen2.5-7b", "name": "Qwen 2.5 7B", "repo": "Qwen/Qwen2.5-7B-Instruct", "desc": "Strong coding 7B", "vram_est": 15},
        {"id": "custom", "name": "Custom Model", "repo": "", "desc": "Enter your own", "vram_est": 8}
    ]

    print("\n--- Step 1: Select Planner Model for GPU 0 (RTX 3090 24GB) ---")
    selected_heavy = prompt_choice("Choose the Heavy Inference model for Planning/QA:", heavy_models)

    if selected_heavy['id'] == 'custom':
        selected_heavy['repo'] = input("Enter HuggingFace Repo ID (e.g., meta-llama/Llama-3.1-8B): ")
        quant = input("Does it need AWQ/GPTQ quantization to fit in 24GB? (y/N): ").lower()
        selected_heavy['quant'] = "awq" if quant == 'y' else None

    print("\n--- Step 2: Select Worker Models for GPU 1 (RTX 5060ti 16GB) ---")
    print("You can load multiple smaller models on GPU 1 (up to ~15GB total VRAM usage).")
    selected_lights = []
    current_vram = 0

    while True:
        if current_vram >= 15:
            print(f"Warning: Estimated VRAM usage ({current_vram}GB) is close to the 16GB limit.")
            break

        print(f"\nCurrent GPU 1 VRAM Est: {current_vram}GB / 16GB")
        add_more = input("Add a worker model to GPU 1? (y/n): ").lower()
        if add_more != 'y': break

        light = prompt_choice("Choose a Light Inference model for execution tasks:", light_models)

        # Clone dict to allow multiple identical custom selections
        selected_model = dict(light)

        if selected_model['id'] == 'custom':
            selected_model['repo'] = input("Enter HuggingFace Repo ID: ")
            selected_model['id'] = selected_model['repo'].split('/')[-1].lower()
            try:
                selected_model['vram_est'] = int(input("Estimated VRAM required in GB (e.g., 8): "))
            except ValueError:
                selected_model['vram_est'] = 8

        selected_lights.append(selected_model)
        current_vram += selected_model['vram_est']

    if not selected_lights:
        print("At least one worker model is required. Defaulting to Exaone 1.2B.")
        selected_lights.append(light_models[0])

    # --- Generate docker-compose.models.yml ---
    compose_dict = {
        'version': '3.8',
        'services': {}
    }

    litellm_models = []

    # Heavy Model (GPU 0)
    heavy_service = {
        'image': 'vllm/vllm-openai:latest',
        'container_name': f'vllm_heavy_{selected_heavy["id"]}',
        'runtime': 'nvidia',
        'ports': ['8000:8000'],
        'environment': ['CUDA_VISIBLE_DEVICES=0', 'HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}'],
        'volumes': ['~/.cache/huggingface:/root/.cache/huggingface'],
        'restart': 'unless-stopped',
        'command': f'--model {selected_heavy["repo"]} --gpu-memory-utilization 0.95 --max-model-len {selected_heavy["max_len"]} --port 8000'
    }
    if selected_heavy["quant"]:
        heavy_service['command'] += f' --quantization {selected_heavy["quant"]}'

    compose_dict['services']['vllm-heavy'] = heavy_service

    # Heavy model is always mapped to the "planner-model" alias in LiteLLM
    litellm_models.append({
        'model_name': 'planner-model',
        'litellm_params': {
            'model': f'openai/{selected_heavy["repo"]}',
            'api_base': 'http://vllm-heavy:8000/v1',
            'api_key': 'sk-dummy-key',
            'rpm': 1000
        }
    })

    # Light Models (GPU 1)
    base_port = 8001
    for idx, light in enumerate(selected_lights):
        service_name = f'vllm-light-{idx}'
        port = base_port + idx

        light_service = {
            'image': 'vllm/vllm-openai:latest',
            'container_name': f'vllm_light_{light["id"]}_{idx}',
            'runtime': 'nvidia',
            'ports': [f'{port}:8000'],
            'environment': ['CUDA_VISIBLE_DEVICES=1', 'HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}'],
            'volumes': ['~/.cache/huggingface:/root/.cache/huggingface'],
            'restart': 'unless-stopped',
            'command': f'--model {light["repo"]} --gpu-memory-utilization 0.90 --max-model-len 4096 --port 8000'
        }

        # If loading multiple models on one GPU, VLLM needs help with memory chunking,
        # but for simplicity we rely on gpu-memory-utilization.
        if len(selected_lights) > 1:
            # Distribute VRAM fraction based on estimate
            fraction = light['vram_est'] / 16.0
            fraction = max(0.1, min(0.95, fraction)) # clamp
            light_service['command'] = light_service['command'].replace('0.90', f'{fraction:.2f}')

        compose_dict['services'][service_name] = light_service

        litellm_models.append({
            'model_name': f'worker-{light["id"]}',
            'litellm_params': {
                'model': f'openai/{light["repo"]}',
                'api_base': f'http://{service_name}:8000/v1',
                'api_key': 'sk-dummy-key',
                'rpm': 5000
            }
        })

    # Write files
    with open('docker-compose.models.yml', 'w') as f:
        yaml.dump(compose_dict, f, sort_keys=False, default_flow_style=False)

    litellm_config = {
        'model_list': litellm_models,
        'router_settings': {
            'routing_strategy': 'usage-based-routing',
            'enable_pre_call_checks': True
        },
        'general_settings': {
            'master_key': 'sk-1234',
            'database_url': 'postgresql://agent_user:agent_pass@postgres:5432/agent_db'
        }
    }

    with open('litellm_config.yaml', 'w') as f:
        yaml.dump(litellm_config, f, sort_keys=False, default_flow_style=False)

    print("\n✅ Configuration generated successfully!")
    print("Files created/updated: docker-compose.models.yml, litellm_config.yaml")
    print("\nTo start the infrastructure, run:")
    print("docker-compose -f docker-compose.yml -f docker-compose.models.yml up -d")

if __name__ == "__main__":
    main()