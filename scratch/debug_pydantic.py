import sys
import pydantic.v1 as pydantic_v1

print(f"Pydantic V1 Version: {pydantic_v1.VERSION}")
print(f"Python Version: {sys.version}")

try:
    from llama_index.core import VectorStoreIndex
    print("llama_index.core.VectorStoreIndex imported")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
