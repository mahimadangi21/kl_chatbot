import os
import logging
from typing import List, Generator
from dotenv import load_dotenv

from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    StorageContext, 
    load_index_from_storage, 
    Settings,
    PromptTemplate
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core.postprocessor import SimilarityPostprocessor, MetadataReplacementPostProcessor
import google.generativeai as genai
# try:
#     from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
#     HAS_RERANKER = True
# except ImportError:
#     HAS_RERANKER = False
#     print("[WARN] FlagEmbeddingReranker not available. Skipping reranking.")
HAS_RERANKER = False

from llama_index.core.query_engine import RetrieverQueryEngine

from src.query_handler import QueryHandler
from src.answer_validator import AnswerValidator
from src.llm_manager import LLMManager

load_dotenv()

# ── CONFIGURATION ──────────────────────────────────────────────────
PERSIST_DIR = "./storage"
DATA_DIR = "./knowledge_base"

# Initialize Settings
Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
# Explicitly set Gemini as default to prevent LlamaIndex from trying to use Groq anywhere
gemini_model = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
if not gemini_model.startswith("models/"):
    gemini_model = f"models/{gemini_model}"

try:
    Settings.llm = Gemini(
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name=gemini_model,
        temperature=0.1
    )
except Exception as e:
    print(f"[WARN] Gemini initialization failed: {e}. Falling back to default.")
    Settings.llm = Gemini(
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name="models/gemini-2.0-flash",
        temperature=0.1
    )

def get_llm(provider="gemini"):
    # Groq is handled directly via SDK in llm_manager, so this only returns Gemini for LlamaIndex
    return LLMManager.get_gemini_llm()

def build_index():
    kb_path = DATA_DIR
    # Restrict to these specific PDFs as requested
    ALLOWED_FILES = ["Email etiquette.pdf", "mahima_dangi_contract.pdf", "data-ai-ethics-policy.pdf"]
    files = [f for f in os.listdir(kb_path) if f in ALLOWED_FILES]
    print(f"Restricted Files in {kb_path}: {files}")
    
    if not files:
        print(f"ERROR: No allowed PDFs found in {kb_path}!")
        print(f"Please ensure {', '.join(ALLOWED_FILES)} are in {kb_path}/")
        return None

    print(f"Building index from embedded knowledge data in src/knowledge_data.py...")
    from llama_index.core import Document
    try:
        from src.knowledge_data import KNOWLEDGE_BASE
    except ImportError:
        print("ERROR: src/knowledge_data.py not found. Please run extraction script first.")
        return None

    documents = []
    for filename, text in KNOWLEDGE_BASE.items():
        if text.strip():
            doc = Document(
                text=text,
                metadata={"file_name": filename, "source": filename}
            )
            documents.append(doc)
            print(f"[INFO] Loaded {filename} from embedded data ({len(text)} chars)")
        else:
            print(f"[WARN] {filename} in embedded data seems to have no text.")
    
    if not documents:
        print("ERROR: Documents loaded but 0 chunks created or no text extracted!")
        return None
    
    # Step 1: Fix chunking (SentenceSplitter 512/64)
    storage_context = StorageContext.from_defaults()
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        show_progress=True
    )
    
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    return index

def verify_index(index) -> bool:
    """Check if index is valid and contains nodes."""
    try:
        if index is None:
            print("ERROR: Index object is None")
            return False
        
        # Try a test retrieval
        retriever = index.as_retriever(similarity_top_k=1)
        test_nodes = retriever.retrieve("test")
        print(f"Index verified: {len(test_nodes)} nodes found")
        return len(test_nodes) > 0
    except Exception as e:
        print(f"Index verification error: {e}")
        return False

def load_or_build_index():
    if not os.path.exists(PERSIST_DIR):
        return build_index()
    else:
        print("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        return load_index_from_storage(storage_context)

# Global index instance
_INDEX = load_or_build_index()

# ── PROMPT ENGINEERING (Step 2) ───────────────────────────────────

QA_PROMPT_TMPL = (
    "You are an intelligent document assistant. Your job is to answer questions ONLY based on the provided document content.\n\n"
    "## CORE RULES:\n"
    "1. Read the provided CONTEXT thoroughly.\n"
    "2. Answer ONLY from the document content provided.\n"
    "3. If the answer is NOT in the CONTEXT, say exactly: \"This information is not mentioned in the provided document.\"\n"
    "4. Do NOT suggest contacting HR, managers, or external portals.\n"
    "5. For fact questions (dates, names, numbers) -> give SHORT answer ONLY (1-2 lines).\n"
    "6. For policy questions -> give a brief 3-4 line summary. \n"
    "7. Never use bullet points unless necessary.\n"
    "8. Never add unnecessary disclaimers or suggestions.\n\n"
    "CONTEXT:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Question: {query_str}\n"
    "Answer: "
)
QA_PROMPT = PromptTemplate(QA_PROMPT_TMPL)

# ── QUERY ENGINE ──────────────────────────────────────────────────

def get_query_engine(provider="groq"):
    llm = get_llm(provider)
    
    # Step 4: Hybrid Search BM25 + Vector (Optional fallback)
    vector_retriever = _INDEX.as_retriever(similarity_top_k=20, vector_store_query_mode="default")
    
    try:
        from llama_index.core.retrievers import QueryFusionRetriever
        from llama_index.retrievers.bm25 import BM25Retriever
        bm25_retriever = BM25Retriever.from_defaults(index=_INDEX, similarity_top_k=5)
        
        fusion_retriever = QueryFusionRetriever(
            [vector_retriever, bm25_retriever],
            num_queries=1,
            use_async=False,
            similarity_top_k=10, 
            mode="reciprocal_rerank"
        )
        retriever = fusion_retriever
    except Exception as e:
        print(f"[WARN] BM25 initialization failed: {e}. Using vector search only.")
        retriever = vector_retriever
    
    # Step 3: Add similarity cutoff postprocessor (0.1)
    node_postprocessors = [
        SimilarityPostprocessor(similarity_cutoff=0.1),
        MetadataReplacementPostProcessor(target_metadata_key="window")
    ]
    
    if HAS_RERANKER:
        node_postprocessors.insert(1, FlagEmbeddingReranker(model="BAAI/bge-reranker-base", top_n=3))
    
    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever, # Fixed variable name to retriever
        node_postprocessors=node_postprocessors,
        text_qa_template=QA_PROMPT,
        llm=llm,
        streaming=True
    )
    
    return query_engine

def call_gemini_direct(system_instruction: str, user_prompt: str) -> str:
    """Direct Google SDK call for Gemini using system_instruction for strict personification."""
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model_name = os.environ.get("GEMINI_MODEL", "models/gemini-2.0-flash")
        if not model_name.startswith("models/"):
            actual_model = f"models/{model_name}"
        else:
            actual_model = model_name
            
        # Using system_instruction parameter (supported in newer Gemini versions/SDKs)
        model = genai.GenerativeModel(
            model_name=actual_model,
            system_instruction=system_instruction
        )
        
        response = model.generate_content(user_prompt)
        
        if hasattr(response, 'text'):
            answer = response.text
        else:
            answer = response.candidates[0].content.parts[0].text
            
        if not answer or answer.strip() == "":
            return "Empty response received from Gemini."
        
        return answer.strip()
    except Exception as e:
        # Fallback if system_instruction is not supported or fails
        try:
            model = genai.GenerativeModel(actual_model)
            full_prompt = f"{system_instruction}\n\nUSER QUESTION: {user_prompt}"
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except:
            print(f"Gemini direct call failed: {e}")
            raise e

def smart_retrieve(query: str, index):
    """Retrieves nodes and filters them to provide a balanced context from all relevant documents."""
    # Step 1: Broad retrieval across all documents
    retriever = index.as_retriever(similarity_top_k=10)
    raw_nodes = retriever.retrieve(query)
    
    if not raw_nodes:
        return []

    # Sort by score descending
    nodes_sorted = sorted(raw_nodes, 
                   key=lambda x: x.score if hasattr(x, 'score') and x.score is not None else 0, 
                   reverse=True)
    
    # Remove the strict "Single Document" concentration to allow multi-document answers
    
    # Step 2: Complexity Check
    word_count = len(query.split())
    # If it's a very simple fact check, still give at least 2 chunks to be safe
    if word_count <= 4 or any(w in query.lower() for w in ["name", "date", "amt", "salary"]):
        return nodes_sorted[:2]
        
    # For general questions, provide up to 4 chunks to ensure we don't miss info across PDFs
    return nodes_sorted[:4]

def build_smart_context(nodes: list, query: str) -> str:
    """Provides full relevant chunks with clear source markers to prevent data loss while keeping context manageable."""
    context_parts = []
    
    for i, node in enumerate(nodes):
        text = node.node.get_content() if hasattr(node.node, 'get_content') else node.node.text
        if not text:
            continue
            
        clean_text = text.replace('\n', ' ').strip()
        context_parts.append(f"REFERENCE {i+1}:\n{clean_text}")
        
    return "\n\n".join(context_parts)

# ── STREAMING INTERFACE ───────────────────────────────────────────

def generate_response_stream(user_input: str, history: List[dict] = [], manual_lang: str = "English", provider: str = "Groq") -> Generator[str, None, None]:
    """
    Revised streaming response generator for Kadel Lab.
    Implements Intent Detection, Smart Retrieval, Focused Context, and Strict Prompting.
    """
    try:
        print(f"\n{'='*50}\n=== NEW PRECISE ENGINE REQUEST ===\nQuery: {user_input}\nProvider: {provider}\nLanguage: {manual_lang}\n{'='*50}")

        # Step 1: Preprocess through QueryHandler
        processed = QueryHandler.process(user_input, provider.lower())
        if processed.get("intent") == "greeting":
            yield processed["response"]
            return

        query_to_use = processed.get("corrected", user_input)
        q_info = processed.get("type_info", {"type": "general", "instruction": "Answer directly and concisely."})
        print(f"Detected Type: {q_info['type']}")

        # Step 2: Smart Retrieval
        if _INDEX is None:
            yield "Index not loaded. Please Sync Vectors in settings."
            return

        nodes = smart_retrieve(query_to_use, _INDEX)
        print(f"Nodes retrieved: {len(nodes)}")

        if not nodes:
            yield "This information is not available in the training documents. Please try rephrasing your question."
            return

        # Step 3: Build Smart Focused Context
        context = build_smart_context(nodes, query_to_use)
        
        # Step 4: Build Semantic Intent Assistant Prompt (Precise & Accurate)
        system_prompt = f"""You are a strict Data Extraction Assistant for Kadel Lab Training Centre.
Your ONLY mission is to extract the EXACT answer from the provided reference documents.

RULES:
1. {q_info['instruction']} 
2. DIRECT ANSWER ONLY: Provide ONLY the specific value requested. 
3. NO DISCLAIMERS: Never say "Based on the document" or "I found...". 
4. NO QUESTIONS: Never repeat the user's question or generate your own response headers.
5. NO EXPLANATIONS: Do not explain what you are doing or what is not in the text.
6. IF NOT FOUND: Say "I could not find this information in the records." and nothing else.

REFERENCE CONTENT:
{context}"""

        user_query_msg = f"Question: {user_input}"

        # Step 5: Execute with Provider Logic & Fallback
        answer = ""
        actual_provider = provider.lower()
        
        try:
            if actual_provider == "groq":
                answer = LLMManager.call_groq_direct(system_prompt, user_query_msg)
            else:
                answer = call_gemini_direct(system_prompt, user_query_msg)
        except Exception as e:
            print(f"Primary provider failed. Falling back...")
            try:
                if actual_provider == "groq":
                    answer = call_gemini_direct(system_prompt, user_query_msg)
                else:
                    answer = LLMManager.call_groq_direct(system_prompt, user_query_msg)
            except Exception as e2:
                yield f"AI service error: {str(e2)}"
                return

        # POST-PROCESSING: Remove any context markers the AI might have copied
        bad_phrases = ["REFERENCE", "--- EXTRACT FROM", "PDF EXTRACTS", "CONTEXT FROM PDFS", "Chunk"]
        lines = answer.split('\n')
        clean_lines = []
        for line in lines:
            if not any(phrase in line for phrase in bad_phrases):
                clean_lines.append(line)
        answer = "\n".join(clean_lines).strip()

        if not answer or len(answer.strip()) < 5:
            yield "The AI could not generate a valid answer. Please try rephrasing your question."
            return

        # Step 6: Add formatted source attribution (User's specific format)
        all_sources = list(set([n.node.metadata.get('file_name', 'document') for n in nodes]))
        answer += f"\n\nSource: {', '.join(all_sources)}"

        # Step 7: Stream out the final answer (simulated typewriter)
        words = answer.split(' ')
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            
        print(f"=== END DEBUG ===\n")

    except Exception as e:
        # Final safety for Windows printing
        try:
            print(f"CRITICAL ERROR in generate_response_stream: {str(e).encode('ascii', 'ignore').decode('ascii')}")
        except:
            print("CRITICAL ERROR in generate_response_stream: [Encoding Error in Message]")
        yield f"An error occurred: {str(e)}"
