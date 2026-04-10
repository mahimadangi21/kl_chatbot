import os
import google.generativeai as genai
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

# ── Gemini Client Setup ───────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
if GEMINI_MODEL in ["gemini-1.5-flash", "gemini-1.5-flash-latest"]:
    GEMINI_MODEL = "gemini-2.5-flash"
KNOWLEDGE_DIR = "knowledge_base"

# ── Document Context ───────────────────────────────────────────────────
# Import pre-extracted text (extracted locally, committed to repo)
# This ensures Railway/HuggingFace deployments have document content
# even without Git LFS support.
try:
    from knowledge_base_text import KNOWLEDGE_BASE_TEXT
    DOCUMENT_CONTEXT = KNOWLEDGE_BASE_TEXT
    print(f"[INFO] Loaded knowledge base from pre-extracted text: {len(DOCUMENT_CONTEXT)} chars")
except ImportError:
    # Fallback: try reading PDFs at runtime
    print("[WARN] knowledge_base_text.py not found. Trying to read PDFs directly...")
    DOCUMENT_CONTEXT = ""
    if os.path.exists(KNOWLEDGE_DIR):
        from pypdf import PdfReader
        for filename in os.listdir(KNOWLEDGE_DIR):
            if filename.endswith(".pdf"):
                try:
                    reader = PdfReader(os.path.join(KNOWLEDGE_DIR, filename))
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            DOCUMENT_CONTEXT += text + "\n"
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    if not DOCUMENT_CONTEXT:
        print("[ERROR] No document context could be loaded!")


# ── System Prompt ───────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Kadel Lab Assistant — a professional AI assistant for Kadel Lab Training Centre.

STRICT RULES:
1. Provide the exact answer relying ONLY on the document context provided in the user's message.
2. Do NOT invent or make up information. If the answer is not found in the context, say: "I don't have that specific information. Please contact HR."
3. Be direct, concise, and professional.
4. Do NOT repeat the question back before answering."""

def _build_messages(user_input: str, history: list, language: str):
    lang_instruction = ""
    if language == "Hindi":
        lang_instruction = " Always respond in Hindi (Devanagari script)."
    elif language == "Hinglish":
        lang_instruction = " Always respond in Hinglish (mix of Hindi and English)."

    system_instruction = SYSTEM_PROMPT + lang_instruction
    
    # Gemini uses 'user' and 'model' roles
    gemini_history = []
    for msg in history[-6:]:
        if msg.get("role") and msg.get("content"):
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

    user_payload = f"DOCUMENT CONTEXT:\n{DOCUMENT_CONTEXT}\n\nQUESTION: {user_input}"
    
    return system_instruction, gemini_history, user_payload


def generate_response(user_input: str, history: list = [], language: str = "English") -> str:
    system_instruction, gemini_history, user_payload = _build_messages(user_input, history, language)
    
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system_instruction
    )
    
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(user_payload, generation_config={"temperature": 0.1})
    
    return response.text

def generate_response_stream(user_input: str, history: list = [], language: str = "English"):
    system_instruction, gemini_history, user_payload = _build_messages(user_input, history, language)
    
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system_instruction
    )
    
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(user_payload, stream=True, generation_config={"temperature": 0.1})

    for chunk in response:
        if chunk.text:
            yield chunk.text
