from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
import os
from src.rag_engine import load_index, get_query_engine, build_index, setup_models
from src.language_handler import detect_language, translate_to_english, translate_response
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── INITIALIZATION ──────────────────────────────────────────────────
index = load_index()
# Global engine will be updated dynamically
query_engine = get_query_engine(index)

class ChatRequest(BaseModel):
    message: str
    history: List[dict]
    auto_detect: bool = False
    manual_lang: str = "English"
    model: str = "Ollama"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    async def event_generator():
        global query_engine
        
        # ── DYNAMIC PROVIDER SWITCHING ──
        # Map frontend model selection to backend provider
        requested_model = request.model.lower()
        requested_provider = "ollama"
        if "groq" in requested_model or "grok" in requested_model:
            requested_provider = "groq"
        elif "gemini" in requested_model:
            requested_provider = "gemini"
            
        # Check current loaded provider (force re-setup if different)
        # We'll use a local check to avoid env var caching issues
        try:
            from llama_index.core.settings import Settings
            current_llm_type = Settings.llm.__class__.__name__.lower()
            
            needs_switch = False
            if requested_provider == "groq" and "groq" not in current_llm_type: needs_switch = True
            if requested_provider == "ollama" and "ollama" not in current_llm_type: needs_switch = True
            if requested_provider == "gemini" and "gemini" not in current_llm_type: needs_switch = True
            
            if needs_switch:
                print(f"Switching LLM to: {requested_provider}")
                setup_models(requested_provider)
                query_engine = get_query_engine(index)
        except Exception as e:
            print(f"Switch Error: {e}")

        message = request.message
        user_lang = request.manual_lang.lower() if request.manual_lang != "English" else 'en'
        
        if request.auto_detect:
            try:
                detected = detect_language(message)
                if detected != 'en': user_lang = detected
            except: pass
            
        eng_query = message
        if user_lang != 'en':
            yield json.dumps({"status": "Translating query..."}) + "\n"
            eng_query = translate_to_english(message, user_lang)

        # ── EXTENDED GREETING LIST ──
        greetings = [
            'hello', 'hi', 'hey', 'hy', 'hlo', 'yo', 'heyo', 'namaste', 
            'start', 'starting', 'ola', 'hola', 'hi there', 'hello there',
            'kaisa ho', 'kya haal', 'kaise ho'
        ]
        is_greeting = any(g in eng_query.lower().strip() for g in greetings) and len(eng_query.split()) < 4

        lang_instruction = "Answer in English."
        if request.manual_lang == "Hindi":
            lang_instruction = "IMPORTANT: You MUST answer in pure Hindi (Devanagari script)."
        elif request.manual_lang == "Hinglish":
            lang_instruction = "IMPORTANT: Answer in Hinglish (a mix of Hindi and English). Use a casual, friendly tone."

        system_instruction = f"Role: You are Kadel Lab Assistant. Brand: Kadel Lab Training Centre. Model Identity: {request.model}. {lang_instruction} Response Guidelines: 1. If it is a greeting, respond warmly as Kadel Lab AI. 2. For academic questions, use provided context. 3. Be concise."
        
        yield json.dumps({"status": f"Querying {request.model.capitalize()}..."}) + "\n"
        
        try:
            if is_greeting:
                # Bypass RAG retrieval and use standard LLM for greetings
                from llama_index.core.settings import Settings
                response = Settings.llm.complete(f"{system_instruction}\n\nUser: {eng_query}")
                full_response = str(response)
                yield json.dumps({"delta": full_response}) + "\n"
            else:
                print(f"Executing RAG query: {eng_query}")
                streaming_response = query_engine.query(eng_query)
                full_response = ""
                for text in streaming_response.response_gen:
                    full_response += text
                    yield json.dumps({"delta": text}) + "\n"
                    await asyncio.sleep(0.01)
                
            if user_lang != 'en' and not is_greeting:
                yield json.dumps({"status": "Translating response..."}) + "\n"
                final_translated = translate_response(full_response, user_lang)
                yield json.dumps({"final_translation": final_translated}) + "\n"
        
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/transcribe")
async def transcribe_endpoint():
    from src.voice_handler import record_and_transcribe
    try:
        text = record_and_transcribe("en-US")
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_endpoint():
    global index, query_engine
    try:
        index = build_index()
        query_engine = get_query_engine(index)
        return {"status": "success", "message": "Knowledge base synchronized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provider")
async def get_provider():
    from llama_index.core.settings import Settings
    llm_name = Settings.llm.__class__.__name__
    return {"provider": llm_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
