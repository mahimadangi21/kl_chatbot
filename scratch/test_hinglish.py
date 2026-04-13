
import os
import sys
import io
from dotenv import load_dotenv

# Windows Encoding Fix
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add the root directory to sys.path to import src
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

from src.rag_engine import generate_response_stream

load_dotenv()

def test_hinglish():
    query = "Data ethics principles kya hain?"
    print(f"Testing Hinglish Query: {query}")
    
    # Test with manual_lang="Hinglish"
    print("\n--- Testing with manual_lang='Hinglish' ---")
    response_gen = generate_response_stream(query, manual_lang="Hinglish", provider="Groq")
    full_response = ""
    for chunk in response_gen:
        full_response += chunk
    print(f"Response: {full_response}")

if __name__ == "__main__":
    test_hinglish()
