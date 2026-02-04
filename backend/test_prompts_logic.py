from app.domain.prompts import get_chat_system_prompt, normalize_language

languages_to_test = ["es", "es-ES", "es-419", "en", "en-US", "fr", None, ""]

print(f"{'Input':<10} | {'Normalized':<10} | {'Prompt Language Sample'}")
print("-" * 50)

for lang in languages_to_test:
    norm = normalize_language(lang)
    prompt = get_chat_system_prompt(lang)
    
    # Check if we got Spanish or English prompt
    is_spanish = "Eres 'La Guía'" in prompt
    lang_label = "SPANISH" if is_spanish else "ENGLISH"
    
    print(f"{str(lang):<10} | {norm:<10} | {lang_label}")
