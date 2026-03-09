import os
import psutil
from typing import Dict, Any, List, Optional
from openai import OpenAI

try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_SMI_AVAILABLE = True
except Exception:
    NVIDIA_SMI_AVAILABLE = False

class LLMClient:
    def __init__(self, base_url: str = None, api_key: str = None, model: str = None):
        # Fallback to environment variables if not provided
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "EMPTY")
        self.model = model or os.getenv("LLM_MODEL_NAME", "Exaone-4.0-32b")
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def get_vram_usage(self) -> Dict[str, Any]:
        """Returns VRAM usage if NVIDIA GPU is available."""
        if not NVIDIA_SMI_AVAILABLE:
            return {"status": "unavailable"}

        try:
            device_count = pynvml.nvmlDeviceGetCount()
            gpus = []
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_mb = info.total / 1024 / 1024
                used_mb = info.used / 1024 / 1024
                free_mb = info.free / 1024 / 1024
                percent = (used_mb / total_mb) * 100

                name = pynvml.nvmlDeviceGetName(handle)
                # Decode bytes to str if needed
                if isinstance(name, bytes):
                    name = name.decode('utf-8')

                gpus.append({
                    "id": i,
                    "name": name,
                    "total_mb": total_mb,
                    "used_mb": used_mb,
                    "free_mb": free_mb,
                    "percent_used": percent
                })

            # Check if any GPU is over 90% used
            warning = any(gpu["percent_used"] > 90 for gpu in gpus)
            return {"status": "ok", "gpus": gpus, "warning": warning}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_response(self, prompt: str, history: List[Dict[str, str]], rag_context: str = "") -> str:
        """
        Generates a response using the local LLM.
        Includes chat history and RAG context if provided.
        """
        messages = []

        # System prompt with RAG context
        system_content = "You are a helpful, intelligent AI assistant."
        if rag_context:
            system_content += f"\n\nHere is some context that might be helpful:\n{rag_context}\n\nPlease base your answer on this context if relevant, but do not mention that you were given this context."

        messages.append({"role": "system", "content": system_content})

        # Add history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            # Provide more context based on the error
            error_msg = str(e)
            if "Connection error" in error_msg or "Failed to connect" in error_msg:
                return f"**[연결 오류]** 로컬 LLM 서버({self.base_url})에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.\n\n상세 오류: `{error_msg}`"
            elif "model" in error_msg.lower():
                return f"**[모델 오류]** 모델 '{self.model}'을(를) 찾을 수 없거나 로드되지 않았습니다.\n\n상세 오류: `{error_msg}`"
            else:
                return f"**[응답 오류]** LLM 처리 중 문제가 발생했습니다.\n\n상세 오류: `{error_msg}`"
