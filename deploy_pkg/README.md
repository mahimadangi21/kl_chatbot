---
title: Kadel Lab Assistant
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Kadel Lab Assistant

A multi-model RAG (Retrieval-Augmented Generation) chatbot for Kadel Lab Training Centre.

## Features
- **Multi-Model Support:** Switch between Groq, Gemini, and Ollama.
- **Multilingual:** Supports English, Hindi, and Hinglish.
- **Modern UI:** Built with React, Tailwind CSS, and Framer Motion.
- **Direct Answers:** Optimized RAG engine for accurate document retrieval.

## Deployment on Hugging Face Spaces
1. Create a new Space on Hugging Face.
2. Select **Docker** as the SDK.
3. Upload this repository.
4. Go to **Settings > Variables and Secrets** and add your API keys:
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
   - `LLM_PROVIDER` (Set to `groq`)
   - `GROQ_MODEL` (e.g., `llama-3.3-70b-versatile`)

## Local Development
```bash
# Terminal 1: Backend
python api.py

# Terminal 2: Frontend
cd ui
npm run dev
```
