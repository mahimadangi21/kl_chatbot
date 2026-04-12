import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from rag_engine import _find_best_section, KEYWORD_MAP, KB_SECTIONS

query = "what is start date of contract"
section = _find_best_section(query)

print(f"Query: {query}")
print(f"Selected Section: {section[:200]}...")

# Check scores manually
query_lower = query.lower()
for doc, keywords in KEYWORD_MAP.items():
    score = sum(1 for kw in keywords if kw in query_lower)
    print(f"Doc: {doc}, Score: {score}")
