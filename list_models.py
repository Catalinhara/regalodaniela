"""List available Gemini models"""
from dotenv import load_dotenv
load_dotenv()

from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_AI_API_KEY"))

print("Available Gemini models:")
print("=" * 60)

try:
    for model in client.models.list():
        if 'gemini' in model.name.lower():
            print(f"✓ {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"  Methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")
