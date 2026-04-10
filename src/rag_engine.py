import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

# ── Groq Client Setup ───────────────────────────────────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
KNOWLEDGE_DIR = "knowledge_base"

# ── Document Loader ───────────────────────────────────────────────────
def load_document_context():
    """Reads all PDFs in the knowledge base and concatenates their text."""
    context_text = ""
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"Warning: {KNOWLEDGE_DIR} not found.")
        return ""
    
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            try:
                reader = PdfReader(filepath)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        context_text += text + "\n"
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                
    # Llama 3 70B on Groq supports 131k tokens (~500,000 characters)
    # We can comfortably pass almost all the text directly into the system prompt!
    max_chars = 300000 
    if len(context_text) > max_chars:
        context_text = context_text[:max_chars]
        
    return context_text

# Load document context once on startup
DOCUMENT_CONTEXT = load_document_context()

# ── System Prompt ───────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are the Kadel Lab Assistant — a professional AI assistant for Kadel Lab Training Centre.

Your role is to strictly answer questions based on the document context provided below.

DOCUMENT CONTEXT:
-----------------
{DOCUMENT_CONTEXT}
-----------------

STRICT RULES:
1. Provide the exact answer relying ONLY on the document context.
2. Do NOT invent or make up information. If the answer is not found in the context, say: "I don't have that specific information. Please contact HR."
3. Be direct, concise, and professional.
4. Do NOT repeat the question back before answering."""


def generate_response(user_input: str, history: list = [], language: str = "English") -> str:
    """Generate a response using Groq API directly."""
    
    lang_instruction = ""
    if language == "Hindi":
        lang_instruction = " Always respond in Hindi (Devanagari script)."
    elif language == "Hinglish":
        lang_instruction = " Always respond in Hinglish (mix of Hindi and English)."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + lang_instruction}
    ]

    # Add conversation history (last 6 messages for context)
    for msg in history[-6:]:
        if msg.get("role") in ["user", "assistant"] and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=512
    )

    return response.choices[0].message.content


def generate_response_stream(user_input: str, history: list = [], language: str = "English"):
    """Streaming version — yields text chunks."""
    
    lang_instruction = ""
    if language == "Hindi":
        lang_instruction = " Always respond in Hindi (Devanagari script)."
    elif language == "Hinglish":
        lang_instruction = " Always respond in Hinglish (mix of Hindi and English)."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + lang_instruction}
    ]

    for msg in history[-6:]:
        if msg.get("role") in ["user", "assistant"] and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_input})

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=512,
        stream=True
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
