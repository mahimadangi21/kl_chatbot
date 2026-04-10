import os
from dotenv import load_dotenv
from llama_index.llms.groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print(f"API Key: {api_key[:10]}...")

try:
    llm = Groq(model="llama3-70b-8192", api_key=api_key)
    response = llm.complete("Hello, say 'Groq is active'")
    print(response)
except Exception as e:
    print(f"Error: {e}")
