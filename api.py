from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import json
import asyncio
import os
import sys
import io

# Windows Encoding Fix
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
from src.rag_engine import generate_response_stream, _INDEX, verify_index
from src.query_handler import QueryHandler
# Temporarily disabled due to Pydantic v1 / Python 3.14 compatibility issue
# try:
#     from langdetect import detect
# except:
#     detect = None
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

# Removed redundant GREETINGS - now handled by QueryHandler

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    async def event_generator():
        try:
            msg = request.message.strip()
            lang = request.manual_lang
            provider = request.model.lower()

            # Step 1: Preprocess and Intent Detection
            processed = QueryHandler.process(msg, provider)
            
            if processed.get("intent") == "greeting":
                yield json.dumps({"delta": processed["response"]}) + "\n"
                return

            yield json.dumps({"status": "Thinking..."}) + "\n"

            # Use corrected/expanded query
            query_to_use = processed.get("corrected", msg)

            for chunk in generate_response_stream(query_to_use, request.history, lang, request.model):
                yield json.dumps({"delta": chunk}) + "\n"
                await asyncio.sleep(0.01)

        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")}

# Serve pre-built React UI
if os.path.exists("ui/dist"):
    app.mount("/", StaticFiles(directory="ui/dist", html=True), name="ui")
else:
    @app.get("/")
    async def root():
        return {"message": "Kadel Lab Assistant API is running."}

if __name__ == "__main__":
    import uvicorn
    
    # Startup Verification
    if not verify_index(_INDEX):
        print("\n" + "!"*50)
        print("WARNING: Index is empty or failed to load!")
        print("Please add documents to 'knowledge_base/' and Sync Vectors.")
        print("!"*50 + "\n")
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
