import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ───────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Normalize old model names to current ones
if GEMINI_MODEL in ["gemini-1.5-flash", "gemini-1.5-flash-latest"]:
    GEMINI_MODEL = "gemini-2.5-flash"

# ── Document Context ───────────────────────────────────────────────────
try:
    from knowledge_base_text import KNOWLEDGE_BASE_TEXT
    DOCUMENT_CONTEXT = KNOWLEDGE_BASE_TEXT
    print(f"[INFO] Loaded knowledge base: {len(DOCUMENT_CONTEXT)} chars")
except ImportError:
    print("[WARN] knowledge_base_text.py not found. No document context available.")
    DOCUMENT_CONTEXT = ""

# ── System Prompt ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Kadel Lab Assistant — a professional AI assistant for Kadel Lab Training Centre.

The DOCUMENT CONTEXT in each user message contains multiple labeled sections (=== document name ===).

INSTRUCTIONS:
1. Read the user's question carefully and identify which document section is MOST RELEVANT.
2. Answer ONLY from the content in that specific section.
3. If data ethics or AI ethics is asked, look in the 'data-ai-ethics-policy' section.
4. If POSH or sexual harassment is asked, look in 'posh-policy' section.
5. If contract terms, notice period, or salary is asked, look in 'mahima_dangi_contract' section.
6. If email etiquette is asked, look in 'Email etiquette' section.
7. If data privacy or GDPR is asked, look in 'Module-4-Data-privacy' section.
8. NEVER make up information. If the answer is truly not in the documents, say: "I don't have that specific information. Please contact HR."
9. Be direct and concise. Do NOT repeat the question."""

def _user_payload(user_input: str) -> str:
    return f"DOCUMENT CONTEXT:\n{DOCUMENT_CONTEXT}\n\nQUESTION: {user_input}"

def _lang_suffix(language: str) -> str:
    if language == "Hindi":
        return " Always respond in Hindi (Devanagari script)."
    elif language == "Hinglish":
        return " Always respond in Hinglish (mix of Hindi and English)."
    return ""

# ── GROQ Engine ─────────────────────────────────────────────────────────
def _groq_stream(user_input, history, language):
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    messages = [{"role": "system", "content": SYSTEM_PROMPT + _lang_suffix(language)}]
    for msg in history[-6:]:
        if msg.get("role") in ["user", "assistant"] and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": _user_payload(user_input)})

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
        stream=True
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ── GEMINI Engine ───────────────────────────────────────────────────────
def _gemini_stream(user_input, history, language):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

    gemini_history = []
    for msg in history[-6:]:
        if msg.get("role") and msg.get("content"):
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT + _lang_suffix(language)
    )
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(
        _user_payload(user_input),
        stream=True,
        generation_config={"temperature": 0.1}
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text

# ── Public Router ───────────────────────────────────────────────────────
def generate_response_stream(user_input: str, history: list = [], language: str = "English", model: str = "Groq"):
    """Routes to Groq or Gemini based on frontend model selection."""
    model_lower = model.lower()
    if "gemini" in model_lower or model_lower == "gemini":
        yield from _gemini_stream(user_input, history, language)
    else:
        # Default to Groq (handles 'Groq', 'Grok', 'groq', etc.)
        yield from _groq_stream(user_input, history, language)

def generate_response(user_input: str, history: list = [], language: str = "English", model: str = "Groq") -> str:
    return "".join(generate_response_stream(user_input, history, language, model))
