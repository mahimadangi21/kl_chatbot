import speech_recognition as sr

def record_and_transcribe(language_code: str = "en-US") -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... speak now")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            text = recognizer.recognize_google(audio, language=language_code)
            print(f"Recognized: {text}")
            return text
        except sr.WaitTimeoutError:
            return "No speech detected. Please try again."
        except sr.UnknownValueError:
            return "Could not understand audio. Please speak clearly."
        except Exception as e:
            return f"Voice error: {str(e)}"

LANG_CODE_MAP = {
    'en': 'en-US', 'hi': 'hi-IN', 'ar': 'ar-SA',
    'fr': 'fr-FR', 'es': 'es-ES', 'de': 'de-DE',
    'zh-cn': 'zh-CN', 'ja': 'ja-JP', 'pt': 'pt-BR'
}
