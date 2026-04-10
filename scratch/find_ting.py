import os
from llama_index.core import SimpleDirectoryReader

docs = SimpleDirectoryReader("knowledge_base").load_data()
for doc in docs:
    if "ting" in doc.text.lower():
        print(f"FOUND IN {doc.metadata.get('file_name')}: {doc.text[:200]}")
