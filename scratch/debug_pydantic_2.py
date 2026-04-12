import sys
import os
from dotenv import load_dotenv
load_dotenv()

print("Testing Gemini import...")
try:
    from llama_index.llms.gemini import Gemini
    print("Gemini imported")
except Exception as e:
    import traceback
    traceback.print_exc()

print("\nTesting Groq import...")
try:
    from groq import Groq
    print("Groq SDK imported")
except Exception as e:
    import traceback
    traceback.print_exc()

print("\nTesting QueryHandler import...")
try:
    from src.query_handler import QueryHandler
    print("QueryHandler imported")
except Exception as e:
    import traceback
    traceback.print_exc()
