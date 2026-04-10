from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import json
import asyncio
import os
from dotenv import load_dotenv
from src.rag_engine import generate_response_stream
try:
    from langdetect import detect
except:
    detect = None

load_dotenv()

app = FastAPI(title="Kadel Lab Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []
    manual_lang: str = "English"
    model: str = "Groq"

# ── GREETING BYPASS ──────────────────────────────────────────────────
GREETINGS = {
    'hello', 'hi', 'hey', 'hy', 'hlo', 'yo', 'heyo', 'namaste',
    'hola', 'hi there', 'hello there', 'kaisa ho', 'kya haal', 'kaise ho'
}

def is_greeting(text: str) -> bool:
    return text.lower().strip() in GREETINGS or \
           (any(g in text.lower() for g in GREETINGS) and len(text.split()) < 4)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    async def event_generator():
        try:
            msg = request.message.strip()
            lang = request.manual_lang

            if is_greeting(msg):
                greet_msg = "Hello! 👋 I'm the Kadel Lab Assistant. How can I help you today?"
                if lang == "Hindi":
                    greet_msg = "नमस्ते! 👋 मैं Kadel Lab Assistant हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?"
                elif lang == "Hinglish":
                    greet_msg = "Hello! 👋 Main Kadel Lab Assistant hoon. Aaj main aapki kaise help kar sakta hoon?"
                yield json.dumps({"delta": greet_msg}) + "\n"
                return

            yield json.dumps({"status": "Thinking..."}) + "\n"

            for chunk in generate_response_stream(msg, request.history, lang):
                yield json.dumps({"delta": chunk}) + "\n"
                await asyncio.sleep(0.01)

        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")}

# Serve pre-built React UI
if os.path.exists("ui/dist"):
    app.mount("/", StaticFiles(directory="ui/dist", html=True), name="ui")
else:
    @app.get("/")
    async def root():
        return {"message": "Kadel Lab Assistant API is running."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
