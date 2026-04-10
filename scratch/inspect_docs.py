from llama_index.core import SimpleDirectoryReader
import sys

# Ensure UTF-8 output for Windows CMD
sys.stdout.reconfigure(encoding='utf-8')

docs = SimpleDirectoryReader("knowledge_base").load_data()
for doc in docs:
    if "contract" in doc.metadata.get("file_name", "").lower():
        print(f"--- {doc.metadata.get('file_name')} ---")
        print(doc.text[:2000]) # More text
