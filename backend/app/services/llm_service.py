import json
import logging
from typing import Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.is_configured = bool(self.api_key and len(self.api_key.strip()) > 0)

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> str | None:
        """Execute chat completion against configured OpenAI-compatible endpoint."""
        if not self.is_configured:
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"LLM request returned status {resp.status_code}: {resp.text}")
                    return None
        except Exception as e:
            logger.warning(f"LLM call failed (falling back to deterministic router): {e}")
            return None

llm_service = LLMService()
