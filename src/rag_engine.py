import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, PromptTemplate
from llama_index.core.settings import Settings
from llama_index.llms.groq import Groq
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# Load environment variables
load_dotenv()

KNOWLEDGE_DIR = "knowledge_base"
PERSIST_DIR = "chroma_db_v3"
EMBED_DIM = 384 # BGE-small is 384

def setup_models(provider=None):
    """Configures the LLM and Embedding models based on .env settings or passed provider."""
    if not provider:
        provider = os.getenv("LLM_PROVIDER", "groq").lower()
    else:
        provider = provider.lower()
    elif provider in ["groq", "grok"]:
        api_key = os.getenv("GROQ_API_KEY")
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY not found in .env — please add it")
        llm = Groq(model=model_name, api_key=api_key, temperature=0.0, max_tokens=512)
        print(f"LLM Provider: groq ({model_name})")
        
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY not found in .env — please add it")
        llm = Gemini(model=f"models/{model_name}", api_key=api_key)
        print(f"LLM Provider: gemini ({model_name})")
        
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    # Use Inference API instead of local Torch to save space and avoid build errors
    hf_token = os.getenv("HF_TOKEN")
    embed_model = HuggingFaceInferenceAPIEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        token=hf_token
    )
    
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.context_window = 32000 # Optimized for Cloud LLMs (Groq/Gemini)
    return llm, embed_model

def build_index():
    setup_models()
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        
    from llama_index.core.node_parser import SentenceSplitter
    parser = SentenceSplitter(chunk_size=1024, chunk_overlap=128)
    
    reader = SimpleDirectoryReader(KNOWLEDGE_DIR)
    documents = reader.load_data()
    nodes = parser.get_nodes_from_documents(documents)

    print(f"Loaded {len(nodes)} document nodes")
    
    faiss_index = faiss.IndexFlatL2(EMBED_DIM)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    index = VectorStoreIndex(
        nodes, storage_context=storage_context
    )
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    print("Index built and saved!")
    return index

def load_index():
    setup_models()
    if not os.path.exists(os.path.join(PERSIST_DIR, "docstore.json")):
        print("No full index found. Building new index...")
        return build_index()
    
    vector_store = FaissVectorStore.from_persist_dir(PERSIST_DIR)
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store, persist_dir=PERSIST_DIR
    )
    index = load_index_from_storage(storage_context=storage_context)
    print("Existing index loaded!")
    return index

def get_query_engine(index):
    qa_prompt_str = (
        "You are an AI that answers questions based on a context. "
        "CONTEXT:\n{context_str}\n\n"
        "QUESTION: {query_str}\n\n"
        "STRICT INSTRUCTION: Provide ONLY the direct, final answer to the QUESTION. "
        "Do NOT repeat the question. Do NOT include phrases like 'Based on the context'. "
        "Do NOT include unrelated legal clauses. Just the answer.\n"
        "ANSWER: "
    )
    qa_prompt = PromptTemplate(qa_prompt_str)
    
    return index.as_query_engine(
        similarity_top_k=3,
        response_mode="simple_summarize", 
        streaming=True,
        text_qa_template=qa_prompt
    )
