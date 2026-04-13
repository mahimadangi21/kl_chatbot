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
    # --- mahima_dangi_contract.pdf ---
    "What is the full name of the candidate mentioned in the contract?",
    "What is the designation/role of Mahima Dangi?",
    "What is the start date of the internship/contract?",
    "What is the duration of the internship mentioned in the document?",
    "Which location is mentioned as the base for the work?",
    "What is the monthly fee/stipend amount for Mahima Dangi?",
    "What is the notice period required for termination of the contract?",
    "Are there any specific working hours mentioned for the intern?",
    
    # --- Email etiquette.pdf ---
    "What are the general rules for professional subject lines in emails?",
    "What is the recommended response time for professional emails?",
    "How should attachments be handled according to email etiquette?",
    "What is the proper way to use 'To', 'Cc', and 'Bcc'?",
    "What should be included in a professional email signature?",
    "Is it acceptable to use emojis or humor in business emails?",
    "What should you do before hitting 'Reply All'?",
    
    # --- data-ai-ethics-policy.pdf ---
    "What are the core principles of the Data & AI Ethics Policy?",
    "How does the policy describe the handling of personal data privacy?",
    "What does the policy say about preventing bias in AI models?",
    "Who is responsible for the ethical implementation of AI according to the document?",
    
    # --- Logical / Combined / Edge Cases ---
    "If Mahima Dangi starts in April 2026, when will the 6-month period end?",
    "Is there any training mentioned regarding email communication for interns?"
]

def run_comprehensive_test():
    print(f"{'='*60}")
    print(f"STARTING COMPREHENSIVE RAG ENGINE TEST (20+ QUESTIONS)")
    print(f"{'='*60}\n")
    
    results = []
    
    for i, q in enumerate(TEST_QUESTIONS):
        print(f"[{i+1}/{len(TEST_QUESTIONS)}] Query: {q}")
        print("-" * 30)
        
        response = ""
        try:
            # We use Gemini for testing as it's generally more stable for large batches
            for token in generate_response_stream(q, history=[], manual_lang="English", provider="Groq"):
                response += token
            
            print(f"Answer: {response}\n")
            results.append({"question": q, "answer": response})
        except Exception as e:
            print(f"ERROR: {str(e)}\n")
            results.append({"question": q, "answer": f"ERROR: {str(e)}"})

    print(f"{'='*60}")
    print(f"TEST COMPLETE. Summary written to scratch/test_results.md")
    print(f"{'='*60}")
    
    # Write results to a markdown file for review
    with open("scratch/test_results.md", "w", encoding="utf-8") as f:
        f.write("# RAG Engine Test Results\n\n")
        f.write("| # | Question | Answer |\n")
        f.write("|---|----------|--------|\n")
        for i, res in enumerate(results):
            # Escaping newlines for table
            clean_ans = res['answer'].replace("\n", " ")
            f.write(f"| {i+1} | {res['question']} | {clean_ans} |\n")

if __name__ == "__main__":
    run_comprehensive_test()
