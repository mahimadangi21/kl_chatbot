from llama_index.core import SimpleDirectoryReader
import sys
sys.stdout.reconfigure(encoding='utf-8')

docs = SimpleDirectoryReader("knowledge_base").load_data()
for doc in docs:
    if "month" in doc.text.lower():
        print(f"FOUND IN: {doc.metadata.get('file_name')}")
        # Find the sentence containing 'month'
        for line in doc.text.split('.'):
            if "month" in line.lower():
                print(f"  > {line.strip()}")
