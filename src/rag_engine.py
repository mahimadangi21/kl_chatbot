import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ───────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
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

# ── Parse document into named sections ────────────────────────────────
def _parse_sections(text: str) -> dict:
    sections = {}
    current_name = None
    current_lines = []
    for line in text.split('\n'):
        if line.startswith('=== ') and line.endswith(' ==='):
            if current_name and current_lines:
                sections[current_name] = '\n'.join(current_lines).strip()
            current_name = line[4:-4].strip()
            current_lines = []
        else:
            if current_name:
                current_lines.append(line)
    if current_name and current_lines:
        sections[current_name] = '\n'.join(current_lines).strip()
    return sections

KB_SECTIONS = _parse_sections(DOCUMENT_CONTEXT)
print(f"[INFO] Parsed {len(KB_SECTIONS)} document sections: {list(KB_SECTIONS.keys())}")

# ── Keyword routing map ────────────────────────────────────────────────
KEYWORD_MAP = {
    'data-ai-ethics-policy.pdf':                    ['ethics', 'ai ethics', 'data ethics', 'principle', 'responsible', 'fairness', 'transparency', 'accountability'],
    'posh-policy.pdf':                              ['posh', 'harassment', 'sexual', 'internal committee', 'complaint', 'respondent', 'victim'],
    'mahima_dangi_contract.pdf':                    ['contract', 'internship', 'stipend', 'salary', 'notice period', 'joining', 'start date', 'end date', 'mahima', 'dangi', 'payment', 'compensation', 'inr', 'rupee', 'pay'],
    'Email etiquette.pdf':                          ['email', 'etiquette', 'professional email', 'reply', 'subject', 'cc', 'bcc'],
    'Module-4-Data-privacy-and-data-protection.pdf': ['privacy', 'gdpr', 'data protection', 'personal data', 'data breach', 'consent', 'rights', 'regulation'],
}

def _find_best_section(user_input: str) -> str:
    query = user_input.lower()
    best_doc = None
    best_score = 0

    for doc_name, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in query)
        if score > best_score:
            best_score = score
            best_doc = doc_name

    if best_doc and best_score > 0 and best_doc in KB_SECTIONS:
        content = KB_SECTIONS[best_doc]
        print(f"[INFO] Routing to: {best_doc} (score={best_score}, len={len(content)})")
        # Return ONLY this section text — no headers to prevent Groq from echoing
        return content

    print("[INFO] No specific section matched — using general fallback")
    # Use first 12000 chars of all docs as fallback
    return DOCUMENT_CONTEXT[:12000]

# ── System Prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an intelligent expert analyst. Your behavior rules:

1. ANALYZE BEFORE ANSWERING
- Carefully read and understand the user's question.
- Identify the exact requirement.
- Do NOT rush to answer.
- Think step-by-step internally before responding.

2. ANSWER ONLY WHAT IS ASKED
- Provide answers strictly limited to the question.
- Do not add unnecessary explanations, filler content, or unrelated details.
- Avoid over-explaining unless explicitly requested.

3. USE CONTEXT OR DOCUMENTS (IF PROVIDED)
- If documents or context are available, extract relevant information.
- Do not copy-paste blindly — understand and then answer.
- Summarize intelligently in your own words.

4. NO ROTE OR GENERIC ANSWERS
- Avoid template-based or memorized responses.
- Every answer must feel thoughtful and context-aware.

5. BE PRECISE AND ACCURATE
- Keep answers clear, to the point, and factually correct.
- If unsure, say "I don't have enough information" instead of guessing.

6. STRUCTURED RESPONSE (WHEN NEEDED)
- Use bullet points or steps if the question requires clarity.
- Keep formatting clean and readable.

7. HANDLE AMBIGUITY SMARTLY
- If the question is unclear, ask a clarifying question instead of assuming.

8. NO HALLUCINATION
- Do not make up facts, data, or references.
- Only rely on given input or verified knowledge.

9. ADAPT RESPONSE LENGTH
- Short question → short answer
- Detailed question → detailed but relevant answer

10. FOCUS ON QUALITY OVER QUANTITY
- Better to give a sharp, correct answer than a long, vague one.

Your goal is to act like a smart human expert who thinks before answering, not like a basic chatbot."""

def _lang_suffix(language: str) -> str:
    if language == "Hindi":
        return " Always respond in Hindi (Devanagari script)."
    elif language == "Hinglish":
        return " Always respond in Hinglish (mix of Hindi and English)."
    return ""

# ── GROQ Engine ────────────────────────────────────────────────────────
def _groq_stream(user_input, history, language):
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    section = _find_best_section(user_input)
    
    sys_content = SYSTEM_PROMPT
    messages = [{"role": "system", "content": sys_content}]
    
    for msg in history[-4:]:
        if msg.get("role") in ["user", "assistant"] and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    prompt = (
        f"--- START OF RELEVANT DOCUMENT CONTEXT ---\n"
        f"{section}\n"
        f"--- END OF RELEVANT DOCUMENT CONTEXT ---\n\n"
        f"As an intelligent analyst, please answer the user's question based strictly on the document context above. Provide a thoughtful answer.\n"
        f"User Question: {user_input}"
    )
    
    if language == "Hindi":
        prompt += "\n(Please respond entirely in Hindi.)"
    elif language == "Hinglish":
        prompt += "\n(Please respond entirely in Hinglish.)"

    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,       
        max_tokens=1024,        
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ── GEMINI Engine ──────────────────────────────────────────────────────
def _gemini_stream(user_input, history, language):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

    section = _find_best_section(user_input)
    sys_content = SYSTEM_PROMPT + _lang_suffix(language)
    
    gemini_history = []
    for msg in history[-4:]:
        if msg.get("role") and msg.get("content"):
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=sys_content
    )
    
    prompt = (
        f"--- START OF RELEVANT DOCUMENT CONTEXT ---\n"
        f"{section}\n"
        f"--- END OF RELEVANT DOCUMENT CONTEXT ---\n\n"
        f"As an intelligent analyst, please answer the user's question based strictly on the document context above. Provide a thoughtful answer.\n"
        f"User Question: {user_input}"
    )
    
    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(
        prompt,
        stream=True,
        generation_config={"temperature": 0.2, "max_output_tokens": 1024}
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text


# ── Public Router ──────────────────────────────────────────────────────
def generate_response_stream(user_input: str, history: list = [], language: str = "English", model: str = "Groq"):
    model_lower = model.lower()
    if "gemini" in model_lower:
        yield from _gemini_stream(user_input, history, language)
    else:
        yield from _groq_stream(user_input, history, language)

def generate_response(user_input: str, history: list = [], language: str = "English", model: str = "Groq") -> str:
    return "".join(generate_response_stream(user_input, history, language, model))
