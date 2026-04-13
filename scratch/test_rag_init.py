from src.rag_engine import _INDEX
if _INDEX:
    print("Index loaded successfully!")
else:
    print("Failed to load index.")
