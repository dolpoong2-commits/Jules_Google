import requests
import json
from openai import OpenAI

def get_vllm_response(endpoint, model, messages, temperature=0.7, max_tokens=1000):
    """
    Call the vLLM OpenAI-compatible API endpoint.
    """
    try:
        # Check if endpoint has /v1, if not, consider it as the base url
        base_url = endpoint if endpoint.endswith('/v1') else f"{endpoint.rstrip('/')}/v1"

        client = OpenAI(
            base_url=base_url,
            api_key="EMPTY"  # vLLM doesn't typically require a real API key
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        return response
    except Exception as e:
        return f"Error connecting to vLLM API: {str(e)}"

def get_openclaw_response(endpoint, messages, temperature=0.7, max_tokens=1000):
    """
    Call the OpenClaw REST API endpoint.
    Assuming OpenClaw accepts a JSON payload with 'messages' or similar format.
    Adjust this function based on the actual OpenClaw API specification.
    """
    try:
        headers = {"Content-Type": "application/json"}

        # Taking the last user message as the prompt for OpenClaw
        # This is a generic implementation. Depending on OpenClaw's API,
        # it might need the full conversation history.
        last_message = messages[-1]['content'] if messages else ""

        # Formatting payload - typical completion format
        # If OpenClaw uses an OpenAI-compatible API, you can use the vLLM function above.
        # Assuming a simple custom REST API here:
        payload = {
            "prompt": last_message,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True
        )
        response.raise_for_status()

        # We handle this as a generator for streaming support if possible,
        # or just return the text
        if response.headers.get('content-type', '').startswith('text/event-stream'):
            return response.iter_lines(decode_unicode=True)
        else:
            # Not streaming
            result = response.json()
            # Try common response formats
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            elif "response" in result:
                return result["response"]
            elif "output" in result:
                return result["output"]
            elif "text" in result:
                return result["text"]
            else:
                return json.dumps(result)

    except Exception as e:
        return f"Error connecting to OpenClaw API: {str(e)}"
