import json
from typing import Dict, Any
from litellm import completion, embedding
from app.core.config import settings

def _get_litellm_kwargs():
    return {
        "api_base": settings.LITELLM_BASE_URL,
        "api_key": settings.LITELLM_API_KEY,
    }

async def generate_summary(text: str) -> str:
    """Generate a summary of the raw text using the main model."""
    prompt = f"""다음 대화 또는 텍스트의 핵심 내용을 요약해줘.
원문:
{text}
요약:"""

    try:
        response = completion(
            model=settings.LLM_MODEL_MAIN,
            messages=[{"role": "user", "content": prompt}],
            **_get_litellm_kwargs()
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Summary generation failed."

async def auto_tag_and_categorize(text: str) -> Dict[str, Any]:
    """Auto-tag and categorize the raw text using the tagging model."""
    prompt = f"""다음 텍스트를 분석하여 아래 JSON 형식으로 분류 정보를 추출해줘. 반드시 JSON 형식만 출력해.
형식:
{{
  "tags": ["태그1", "태그2", "태그3", "태그4"],
  "category_main": "대분류",
  "category_sub": "소분류",
  "importance": "low|normal|high|critical 중 하나",
  "project": "프로젝트 이름 (없으면 null)"
}}

원문:
{text}
"""

    try:
        response = completion(
            model=settings.LLM_MODEL_TAGGING,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            **_get_litellm_kwargs()
        )
        content = response.choices[0].message.content.strip()

        # Parse JSON
        try:
            result = json.loads(content)
            # Ensure basic structure
            return {
                "tags": result.get("tags", []),
                "category_main": result.get("category_main"),
                "category_sub": result.get("category_sub"),
                "importance": result.get("importance", "normal"),
                "project": result.get("project")
            }
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from LLM output: {content}")
            return _default_tagging_response()

    except Exception as e:
        print(f"Error generating tags: {e}")
        return _default_tagging_response()

def _default_tagging_response():
    return {
        "tags": ["Uncategorized"],
        "category_main": "Misc",
        "category_sub": "General",
        "importance": "normal",
        "project": None
    }

async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for the text using the configured embedding model."""
    try:
        response = embedding(
            model=settings.EMBEDDING_MODEL,
            input=text,
            **_get_litellm_kwargs()
        )
        return response.data[0]["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return a zero vector as fallback
        return [0.0] * settings.EMBEDDING_DIM

async def rerank_results(query: str, documents: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Rerank search results using the reranker model.
    Since LiteLLM currently might not have a universal 'rerank' endpoint,
    we either use an LLM call or a specific rerank API if supported.
    For now, this serves as a placeholder or uses a standard LLM to re-evaluate.
    """
    if not documents:
        return []

    # In a real implementation with a dedicated reranker API (like Cohere or BAAI via some endpoint),
    # we would call it here. For now, we simulate or pass-through if not natively supported by the gateway.
    # To keep it simple for the MVP, we just return the documents sorted by their vector score,
    # or you could implement a custom LiteLLM call if the gateway exposes `/rerank`.

    # Placeholder: Return as-is, assuming Qdrant's cosine similarity score is initial ranking.
    # Future: Call BAAI bge-reranker-v2-m3 endpoint here.
    return documents
