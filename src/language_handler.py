from langdetect import detect
from llama_index.core.settings import Settings

SUPPORTED_LANGUAGES = {
    'en': 'English', 'hi': 'Hindi/Hinglish', 'ar': 'Arabic',
    'fr': 'French', 'es': 'Spanish', 'de': 'German',
    'zh-cn': 'Chinese', 'ja': 'Japanese', 'pt': 'Portuguese'
}

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang
    except:
        return 'en'

def translate_to_english(text: str, source_lang: str) -> str:
    if source_lang == 'en':
        return text
    target = 'English'
    if source_lang == 'hi': target = 'Standard English (clear and formal)'
    prompt = f"Translate the following {SUPPORTED_LANGUAGES.get(source_lang, 'text')} text to {target}. Keep all technical terms, names, and academic codes unchanged. Return ONLY the translated text:\n\n{text}"
    response = Settings.llm.complete(prompt)
    return str(response).strip()

def translate_response(text: str, target_lang: str) -> str:
    if target_lang == 'en':
        return text
    lang_name = SUPPORTED_LANGUAGES.get(target_lang, 'English')
    prompt = f"Translate this to {lang_name}. Return only the translation:\n\n{text}"
    response = Settings.llm.complete(prompt)
    return str(response)
