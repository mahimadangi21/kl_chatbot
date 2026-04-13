
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

def test_hindi_query():
    query = "नमस्ते, आप कौन हैं?"
    print(f"Testing Hindi Query: {query}")
    
    # Test with manual_lang="Hindi"
    print("\n--- Testing with manual_lang='Hindi' ---")
    response_gen = generate_response_stream(query, manual_lang="Hindi", provider="Gemini")
    full_response = ""
    for chunk in response_gen:
        full_response += chunk
    print(f"Response: {full_response}")

    query2 = "क्या मुझे ट्रेनिंग के दौरान पैसे मिलेंगे?"
    print(f"\nTesting Hindi Query: {query2}")
    response_gen2 = generate_response_stream(query2, manual_lang="Hindi", provider="Gemini")
    full_response2 = ""
    for chunk in response_gen2:
        full_response2 += chunk
    print(f"Response: {full_response2}")

if __name__ == "__main__":
    test_hindi_query()
