from abc import ABC, abstractmethod
import os
import httpx
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

class GoogleDirectLLMProvider(LLMProvider):
    """
    Direct provider using Google AI SDK for Gemini 2.5 Flash.
    Maximum context: 1M tokens, superior performance.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        # Using gemini-2.5-flash (latest stable, 1M context)
        self.model_id = 'gemini-2.5-flash'
        
    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
        """
        Generate using Google AI SDK directly.
        Uses system_instruction for proper separation of system/user context.
        """
        try:
            # Create prompt with system instruction
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.4,
                    max_output_tokens=max_tokens,
                    safety_settings=[
                        types.SafetySetting(
                            category='HARM_CATEGORY_HARASSMENT',
                            threshold='BLOCK_NONE'
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_HATE_SPEECH',
                            threshold='BLOCK_NONE'
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                            threshold='BLOCK_NONE'
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_DANGEROUS_CONTENT',
                            threshold='BLOCK_NONE'
                        ),
                    ]
                )
            )
            
            return response.text
            
        except Exception as e:
            print(f"ERROR in GoogleDirectLLMProvider: {e}")
            raise e
    
    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate embeddings using Google's embedding model.
        """
        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                content=text
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"ERROR generating embedding with Google: {e}")
            # Fallback to dummy
            import random
            return [random.random() for _ in range(768)]

class GeminiLLMProvider(OpenRouterLLMProvider):
    """
    Fallback provider for Gemini via OpenRouter.
    Used when Google Direct fails or API key not available.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, model="google/gemini-2.0-flash-thinking-exp-01-21") 
        self.model = "google/gemini-2.0-flash-thinking-exp-01-21"

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4, 
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=30.0)
                if response.status_code != 200:
                    print(f"ERROR: OpenRouter (Gemini) returned {response.status_code}: {response.text}")
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"CRITICAL ERROR in GeminiLLMProvider (OpenRouter): {e}")
                raise e

def get_llm_provider() -> LLMProvider:
    """Factory to get the configured provider with fallback chain."""
    
    # Priority 1: Google AI Direct (best context window, lowest cost)
    google_ai_key = os.getenv("GOOGLE_AI_API_KEY")
    if google_ai_key and google_ai_key.strip() and not google_ai_key.startswith("${"):
        try:
            print("INFO: Using GoogleDirectLLMProvider (2M context)")
            return GoogleDirectLLMProvider(api_key=google_ai_key)
        except Exception as e:
            print(f"WARNING: GoogleDirectLLMProvider failed to initialize: {e}")
            print("INFO: Falling back to OpenRouter...")
    
    # Priority 2: OpenRouter (Gemini via proxy, 128k context)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key.strip() and not openrouter_key.startswith("${"):
        print("INFO: Using GeminiLLMProvider via OpenRouter")
        return GeminiLLMProvider(api_key=openrouter_key)
    
    # Priority 3: Mock (development/testing)
    print("WARNING: Using MockLLMProvider (No valid API keys found)")
    return MockLLMProvider()
