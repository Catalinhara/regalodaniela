import os
import sys
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.llm import get_llm_provider, GeminiLLMProvider, MockLLMProvider

async def verify():
    print("--- Verifying LLM Provider Configuration ---")
    
    # Test 1: Check Default (likely Mock if no keys) or OpenRouter if key in env
    provider = get_llm_provider()
    print(f"Current Provider: {type(provider).__name__}")
    
    if isinstance(provider, GeminiLLMProvider):
        print(f"✅ Correctly instantiated GeminiLLMProvider")
        print(f"   Model: {provider.model}")
        if "gemini-2.5-flash-lite" in provider.model:
             print("   ✅ Model ID looks correct (2.5 Flash Lite)")
        else:
             print(f"   ⚠️ Model ID might be unexpected: {provider.model}")
    elif isinstance(provider, MockLLMProvider):
        print("ℹ️ Using MockLLMProvider (No API keys found, which is expected if not set)")
    else:
        print(f"⚠️ Unexpected provider: {type(provider).__name__}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify())
