import os
import sys
import io

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_engine import generate_response_stream
from dotenv import load_dotenv

# Set encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

TEST_QUESTIONS = [
    "What is the full name of the candidate in the contract?",
    "What is the designation of Mahima Dangi?",
    "What is the start date of the contract?",
    "How much is the monthly stipend/fee mentioned?",
    "What is the base location for the work?",
    "What is the notice period for contract termination?",
    "Are overtime fees applicable in this contract?",
    "What is the duration of the internship?",
    "Who is the authorized signatory for the company?",
    "Is there any training mentioned in the contract?"
]

def run_precision_test():
    print(f"{'='*60}")
    print(f"STARTING CONTRACT PRECISION TEST (5-10 QUESTIONS)")
    print(f"{'='*60}\n")
    
    results = []
    
    for i, q in enumerate(TEST_QUESTIONS):
        print(f"[{i+1}/{len(TEST_QUESTIONS)}] Query: {q}")
        
        response = ""
        try:
            # Using Groq for speed and consistency
            for token in generate_response_stream(q, history=[], manual_lang="English", provider="Groq"):
                response += token
            
            response = response.strip()
            print(f"Answer: {response}\n")
            results.append({"question": q, "answer": response})
        except Exception as e:
            print(f"ERROR: {str(e)}\n")
            results.append({"question": q, "answer": f"ERROR: {str(e)}"})

    print(f"{'='*60}")
    print(f"TEST COMPLETE.")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_precision_test()
