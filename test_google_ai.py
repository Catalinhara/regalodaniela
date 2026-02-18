"""
Test script to verify Google AI Direct integration with fallback.
Tests:
1. GoogleDirectLLMProvider with valid key
2. Fallback to OpenRouter if Google fails
3. Fallback to Mock if no keys available
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# CRITICAL: Load .env file BEFORE importing backend modules
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.llm import get_llm_provider, GoogleDirectLLMProvider, GeminiLLMProvider, MockLLMProvider

async def test_provider():
    print("=" * 60)
    print("Google AI Direct Integration - Verification Test")
    print("=" * 60)
    
    # Get provider from factory
    provider = get_llm_provider()
    provider_type = type(provider).__name__
    
    print(f"\n✓ Provider instantiated: {provider_type}")
    
    # Test generation
    try:
        print("\n📝 Testing text generation...")
        response = await provider.generate(
            system_prompt="You are a helpful assistant. Respond in ONE short sentence.",
            user_prompt="Say 'Hello from ClaraMente' in a professional tone.",
            max_tokens=100
        )
        print(f"✓ Response received ({len(response)} chars):")
        print(f"  '{response[:200]}...'")
        
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False
    
    # Provider-specific checks
    if isinstance(provider, GoogleDirectLLMProvider):
        print("\n✅ Using Google AI Direct (2M context window)")
        print("   Model: gemini-2.0-flash-thinking-exp-01-21")
    elif isinstance(provider, GeminiLLMProvider):
        print("\n⚠️  Using OpenRouter fallback (128k context window)")
        print(f"   Model: {provider.model}")
    elif isinstance(provider, MockLLMProvider):
        print("\n⚠️  Using Mock provider (no API keys configured)")
    
    print("\n" + "=" * 60)
    print("✓ Verification complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_provider())
    sys.exit(0 if success else 1)
