"""
Script de debug para verificar la carga de variables de entorno.
"""
import os
import sys

print("=" * 60)
print("DEBUG: Verificación de Variables de Entorno")
print("=" * 60)

# Ver todas las variables de entorno relacionadas con Google
print("\n1. Variables de entorno en el sistema:")
print(f"   GOOGLE_AI_API_KEY = '{os.getenv('GOOGLE_AI_API_KEY')}'")
print(f"   OPENROUTER_API_KEY = '{os.getenv('OPENROUTER_API_KEY')}'")

# Ver el contenido del archivo .env
print("\n2. Contenido del archivo .env:")
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"   Ruta: {env_path}")
print(f"   Existe: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if 'GOOGLE_AI_API_KEY' in line or 'OPENROUTER' in line:
                # Ocultar parte de la clave por seguridad
                display_line = line.strip()
                if '=' in display_line and not display_line.startswith('#'):
                    key, value = display_line.split('=', 1)
                    if len(value) > 10:
                        masked_value = value[:10] + '...' + value[-4:]
                    else:
                        masked_value = value
                    print(f"   Línea {i}: {key}={masked_value}")
                else:
                    print(f"   Línea {i}: {display_line}")

# Verificar si el script está leyendo correctamente
print("\n3. Test de lectura desde el código:")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Simular la lógica del get_llm_provider
google_ai_key = os.getenv("GOOGLE_AI_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")

print(f"   google_ai_key existe: {google_ai_key is not None}")
print(f"   google_ai_key vacía: {not bool(google_ai_key and google_ai_key.strip())}")
if google_ai_key:
    print(f"   google_ai_key comienza con '${{': {google_ai_key.startswith('${')}") 
    print(f"   google_ai_key valor (primeros 15 chars): '{google_ai_key[:15]}...'")
    print(f"   google_ai_key longitud: {len(google_ai_key)}")

print(f"\n   openrouter_key existe: {openrouter_key is not None}")
if openrouter_key:
    print(f"   openrouter_key valor (primeros 15 chars): '{openrouter_key[:15]}...'")

# Verificar la lógica de decisión
print("\n4. Lógica de selección de provider:")
if google_ai_key and google_ai_key.strip() and not google_ai_key.startswith("${"):
    print("   ✓ Debería usar GoogleDirectLLMProvider")
elif openrouter_key and openrouter_key.strip() and not openrouter_key.startswith("${"):
    print("   ✓ Debería usar GeminiLLMProvider (OpenRouter)")
else:
    print("   ✗ Usará MockLLMProvider")
    print(f"     Razón google_ai_key:")
    if not google_ai_key:
        print("       - Variable no existe o es None")
    elif not google_ai_key.strip():
        print("       - Variable está vacía o solo espacios")
    elif google_ai_key.startswith("${"):
        print("       - Variable es un placeholder (${{...}})")
    
print("\n" + "=" * 60)
