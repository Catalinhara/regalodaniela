import asyncio
import os
import sys
# Add parent dir to path so we can import app
sys.path.append(os.getcwd())

from app.services.llm import get_llm_provider

async def main():
    print("Testing LLM Provider...")
    try:
        provider = get_llm_provider()
        print(f"Provider: {provider.__class__.__name__}")
        
        if hasattr(provider, 'api_key'):
            print(f"API Key present: {bool(provider.api_key)}")
            if provider.api_key:
                print(f"API Key prefix: {provider.api_key[:5]}...")
            else:
                print("API Key is empty string")
        else:
            print("Using Mock/Default provider")
        
        print("Attempting generation...")
        res = await provider.generate("System", "Hello check")
        print(f"Response: {res}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
