from abc import ABC, abstractmethod
import os
import httpx
from typing import Optional

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
        """Generates text from the LLM."""
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """Generates a vector embedding for the text."""
        pass

class MockLLMProvider(LLMProvider):
    """
    Dummy provider for dev/testing without eating credits.
    """
    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
        is_spanish = "Español" in system_prompt or "ÚNICAMENTE" in system_prompt
        if is_spanish:
            if "Observación" in system_prompt:
                return "Observación: He notado registros frecuentes. Sugerencia: Continúa así."
            return "Hola, soy El Espejo. ¿En qué puedo ayudarte hoy?"
        
        if "Observation" in system_prompt:
            return "Observation: I noticed you are checking in frequently. This shows commitment. Suggestion: Keep it up."
        return "Hello, I am The Mirror. How can I help you today?"

    async def get_embedding(self, text: str) -> list[float]:
        import random
        # Return 1536-dim dummy vector
        return [random.random() for _ in range(1536)]

class OpenRouterLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "mistralai/mistral-7b-instruct"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.embedding_url = "https://openrouter.ai/api/v1/embeddings"

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173", # Required by OpenRouter for free tier/stats
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,  # Lowered for consistency and grounding
            "max_tokens": max_tokens,
            "stop": ["User:", "\nUser:", "Assistant:", "\nAssistant:"] # Prevent turn simulation only
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=30.0)
                if response.status_code != 200:
                    print(f"ERROR: OpenRouter returned {response.status_code}: {response.text}")
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"CRITICAL ERROR in OpenRouterLLMProvider: {e}")
                raise e

    async def get_embedding(self, text: str) -> list[float]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
        }
        
        # Use a widely supported model for embeddings via OpenRouter if possible, 
        # or fallback to a specific one. 'text-embedding-ada-002' mapping might vary on OR.
        # Let's try to use a standard one.
        payload = {
            "model": "text-embedding-ada-002", # Often available via OpenAI wrapper on OR
            "input": text
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.embedding_url, headers=headers, json=payload, timeout=10.0)
                if response.status_code != 200:
                    # Fallback to dummy if API fails (e.g. model not supported on this route)
                    print(f"WARNING: Embedding API failed {response.status_code}, using dummy.")
                    import random
                    return [random.random() for _ in range(1536)]
                    
                data = response.json()
                return data["data"][0]["embedding"]
            except Exception as e:
                print(f"ERROR generating embedding: {e}")
                import random
                return [random.random() for _ in range(1536)]

def get_llm_provider() -> LLMProvider:
    """Factory to get the configured provider."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Check if key is present and NOT a placeholder/template
    if api_key and api_key.strip() and not api_key.startswith("${"):
        return OpenRouterLLMProvider(api_key=api_key)
    
    print("WARNING: Using MockLLMProvider (API Key missing or invalid placeholder)")
    return MockLLMProvider()
