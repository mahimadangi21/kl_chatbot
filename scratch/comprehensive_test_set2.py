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

# NEW 20 QUESTIONS (Different from previous set)
TEST_QUESTIONS_2 = [
    "What is the specific purpose of the 'Cc' field in the etiquette guide?",
    "What does the contract say about TDS deductions?",
    "What is the recommended sign-off for a professional email if not using a full signature?",
    "How is 'Data Quality' defined in the AI Ethics Policy?",
    "What is the notice period for contract termination by the trainee?",
    "Does the contract define what constitutes 'Confidential Information'?",
    "What is the rule about using 'High Priority' flags in emails?",
    "Does the AI Ethics Policy mention 'Human Oversight' or 'Accountable person'?",
    "What is the specific junction mentioned for the base location?",
    "Is there any mention of a 'minimum period' of service in the contract?",
    "What is the stance on using professional acronyms in business emails?",
    "How does the AI Ethics Policy define 'Transparency'?",
    "What should you do if an email thread becomes too long or complex?",
    "What is the exact currency and symbol used for the service fee?",
    "Does the contract mention ownership of work or Intellectual Property?",
    "What is the policy's view on respect for 'individual autonomy'?",
    "How should you format a subject line for a meaningful email?",
    "Are there specific mentions of providing equipment like laptops?",
    "Does the AI policy address 'bias mitigation' specifically?",
    "What is the advice on 'Reply All' when the response is only for the sender?"
]

def run_new_test():
    print(f"{'='*60}")
    print(f"STARTING COMPREHENSIVE RAG TEST - SET 2 (20 NEW QUESTIONS)")
    print(f"{'='*60}\n")
    
    results = []
    
    for i, q in enumerate(TEST_QUESTIONS_2):
        print(f"[{i+1}/{len(TEST_QUESTIONS_2)}] Query: {q}")
        
        response = ""
        try:
            # Using Groq as requested
            for token in generate_response_stream(q, history=[], manual_lang="English", provider="Groq"):
                response += token
            
            # Clean up response (some models might still add noise)
            response = response.strip()
            print(f"Answer: {response}\n")
            results.append({"question": q, "answer": response})
        except Exception as e:
            print(f"ERROR: {str(e)}\n")
            results.append({"question": q, "answer": f"ERROR: {str(e)}"})

    # Write results to separate file
    with open("scratch/test_results_set2.md", "w", encoding="utf-8") as f:
        f.write("# RAG Engine Test Results - Set 2\n\n")
        f.write("| # | Question | Answer |\n")
        f.write("|---|----------|--------|\n")
        for i, res in enumerate(results):
            clean_ans = res['answer'].replace("\n", " ")
            f.write(f"| {i+1} | {res['question']} | {clean_ans} |\n")

if __name__ == "__main__":
    run_new_test()
