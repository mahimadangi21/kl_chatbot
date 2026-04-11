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
    'mahima_dangi_contract.pdf':                    ['contract', 'internship', 'stipend', 'salary', 'notice period', 'joining', 'start date', 'end date', 'mahima', 'dangi', 'payment', 'compensation', 'inr', 'rupee', 'pay', 'ctc', 'full-time', 'offer'],
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
        print(f"[INFO] Routing to: {best_doc} (score={best_score})")
        # Return a window of the content if it's too large, but for now 3000 chars is safer than 12000
        return content[:3000]

    print("[INFO] No specific section matched — using general fallback")
    # Return a smaller fallback to prevent Groq from getting lost
    return DOCUMENT_CONTEXT[:2500]

# ── System Prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an intelligent AI assistant designed to answer strictly based on provided documents (PDFs) with deep reasoning and analysis.

========================
🧠 CORE BEHAVIOR
========================

1. Do NOT give memorized or generic answers.
2. Always ANALYZE the document content before answering.
3. Think step-by-step internally before responding.
4. Your answers must feel like they are "understood", not copied.

========================
📄 DOCUMENT UNDERSTANDING
========================

When a question is asked:

1. First SEARCH the relevant sections in the PDF.
2. Then UNDERSTAND the meaning (not just keywords).
3. Then REWRITE the answer in your own words.

If exact answer is:
- ✅ FOUND → Answer accurately from document
- ❌ NOT FOUND → Try to infer from related content
- ❌ STILL NOT FOUND → Say:
  "This information is not available in the provided documents."

========================
🧠 LOGICAL REASONING MODE
========================

- If user question is slightly different from document:
  → Match meaning, not exact words
  → Infer logically from related content

- Do NOT hallucinate or make up facts.

- If similar concept exists:
  → Use reasoning to derive the answer

========================
✂️ ANSWER STYLE CONTROL
========================

- If question asks for:
  • Date → Give ONLY the date (no paragraph)
  • Definition → Short and clear
  • Explanation → Medium length
  • List → Bullet points

- Avoid unnecessary long paragraphs
- Be precise and relevant

========================
🚫 HALLUCINATION CONTROL
========================

- NEVER generate fake answers
- NEVER assume facts not in document
- If unsure → clearly say it's not available

========================
🎯 STRICT RESPONSE RULES
========================

- Answer ONLY what is asked
- Do NOT add extra unrelated info
- Keep answers concise but meaningful

========================
⚙️ MODEL BEHAVIOR ALIGNMENT
========================

- Prefer accuracy over creativity
- Prefer document truth over general knowledge
- Be reliable, not imaginative"""

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
    
    # Using a much cleaner, XML-based boundary which Llama-3 respects better
    sys_content = SYSTEM_PROMPT + "\n\nYou are provided with a <context> block below. You must answer the users question based ONLY on that context. Search the context specifically for the subject of the question (e.g. if asked about CTC, ignore dates; if asked about dates, ignore salary)."
    
    messages = [{"role": "system", "content": sys_content}]
    for msg in history[-4:]:
        if msg.get("role") in ["user", "assistant"] and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    prompt = f"<context>\n{section}\n</context>\n\nQuestion: {user_input}\nAnswer:"
    
    if language == "Hindi":
        prompt += " (Answer in Hindi)"
    elif language == "Hinglish":
        prompt += " (Answer in Hinglish)"

    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.0,       
        max_tokens=600,        
        stream=True,
        # Stop sequences prevent the model from hallucinating a Q&A session
        stop=["---", "</context>", "Question:", "User Question:"]
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
        f"As an intelligent analyst, please answer the user's question based strictly on the document context above. Provide a thoughtful answer.\n\n"
        f"SAFETY LAYER: You must be extremely strict about not guessing. If the answer is not clearly supported by the document, do NOT attempt to generate a smart or approximate answer. "
        f"Only infer when there is strong contextual similarity. Otherwise, override your response completely and output EXACTLY: "
        f"\"This information is not available in the provided documents.\"\n"
        f"Accuracy > Completeness.\n\n"
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
