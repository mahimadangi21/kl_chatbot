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
Settings.llm = Gemini(
    api_key=os.getenv("GEMINI_API_KEY"),
    model_name=os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash"),
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

    print(f"Building index from {kb_path} using pdfplumber...")
    import pdfplumber
    from llama_index.core import Document

    documents = []
    for filename in files:
        if filename.lower().endswith(('.pdf', '.txt', '.docx')):
            file_path = os.path.join(kb_path, filename)
            try:
                text = ""
                if filename.lower().endswith('.pdf'):
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            extracted = page.extract_text()
                            if extracted:
                                text += extracted + "\n"
                else:
                    # Fallback for txt/docx
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                
                if text.strip():
                    doc = Document(
                        text=text,
                        metadata={"file_name": filename, "source": filename}
                    )
                    documents.append(doc)
                    print(f"[INFO] Loaded {filename} ({len(text)} chars)")
                else:
                    print(f"[WARN] {filename} seems to have no readable text.")
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
    
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

def call_gemini_direct(context: str, query: str) -> str:
    """Direct Google SDK call for Gemini to ensure correct response extraction."""
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        )
        
        prompt = f"""You are a Training Center Assistant.
Use the following context to answer the question.
If the answer is not in the context, say:
'I could not find this in the training documents.'

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""
        
        response = model.generate_content(prompt)
        
        # CORRECT extraction for Gemini SDK:
        if hasattr(response, 'text'):
            answer = response.text
        else:
            # Fallback for complex response structures
            answer = response.candidates[0].content.parts[0].text
            
        if not answer or answer.strip() == "":
            return "Empty response received from Gemini. Please try again."
        
        return answer.strip()
    except Exception as e:
        print(f"Gemini direct call failed: {e}")
        raise e

def smart_retrieve(query: str, index):
    """Retrieves nodes and filters/limits them based on question complexity and document relevance."""
    # Step 1: Broad retrieval
    retriever = index.as_retriever(similarity_top_k=5)
    raw_nodes = retriever.retrieve(query)
    
    if not raw_nodes:
        return []

    # Sort by score descending
    nodes_sorted = sorted(raw_nodes, 
                   key=lambda x: x.score if hasattr(x, 'score') and x.score is not None else 0, 
                   reverse=True)
    
    # Step 2: High-Score Concentration
    # If the top score is significantly higher than the rest, stick to that document only
    top_score = nodes_sorted[0].score if hasattr(nodes_sorted[0], 'score') else 0
    if top_score > 0.6:
        # If we have a very strong match, only look at that document
        top_doc = nodes_sorted[0].node.metadata.get('file_name')
        nodes_sorted = [n for n in nodes_sorted if n.node.metadata.get('file_name') == top_doc]
    
    # Step 3: Simple Question Limit
    # For short, direct questions, only show the TOP 1 chunk to the AI to prevent confusion
    word_count = len(query.split())
    if word_count <= 5:
        return nodes_sorted[:1]
        
    return nodes_sorted[:3]
        
    return filtered_nodes

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
        system_prompt = f"""You are a specialized Training & Contract Assistant. Your goal is to provide HIGHLY ACCURATE and PRECISE answers based ONLY on the provided document segments.

STRICT GUIDELINES:
1. SEARCH SCOPE: Use ONLY the provided CONTEXT. Do not use external knowledge or general principles.
2. PRECISION: Provide exact details (dates, names, rules). Every different question must have a different, specific answer.
3. NO HALLUCINATION: If the context does not contain the answer, say: "The provided documents do not contain this specific information."
4. CONCISENESS: Keep answers brief (1-3 lines) unless details are requested.
5. INTENT FOCUS: If a question is about a specific policy, do not include unrelated policies.

-----------------------
CONTEXT FROM PDFS:
{context}
-----------------------"""

        user_message = f"QUESTION: {user_input}\n\n-----------------------\n\nFINAL ANSWER:"

        # Step 5: Execute with Provider Logic & Fallback
        answer = ""
        actual_provider = provider.lower()
        
        try:
            if actual_provider == "groq":
                answer = LLMManager.call_groq_direct(system_prompt, user_message)
            else:
                answer = call_gemini_direct(system_prompt, user_message)
        except Exception as e:
            print(f"Primary provider failed. Falling back...")
            try:
                if actual_provider == "groq":
                    answer = call_gemini_direct(system_prompt, user_message)
                else:
                    answer = LLMManager.call_groq_direct(system_prompt, user_message)
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
