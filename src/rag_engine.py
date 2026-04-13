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
    ALLOWED_FILES = ["Email etiquette.pdf", "mahima_dangi_contract.pdf", "data-ai-ethics-policy.pdf", "software_engineering_tutorial.pdf"]
    
    from llama_index.core import SimpleDirectoryReader
    
    # Check for actual PDF files first for higher quality extraction
    available_pdfs = [f for f in os.listdir(kb_path) if f in ALLOWED_FILES and f.endswith('.pdf')]
    
    documents = []
    
    if available_pdfs:
        print(f"[INFO] Found {len(available_pdfs)} physical PDFs. Loading directly for high-fidelity indexing...")
        # Load only allowed files
        reader = SimpleDirectoryReader(
            input_dir=kb_path,
            input_files=[os.path.join(kb_path, f) for f in available_pdfs],
            filename_as_id=True
        )
        documents.extend(reader.load_data())
    else:
        print(f"[WARN] No physical PDFs found. Falling back to embedded knowledge data...")
        from src.knowledge_data import KNOWLEDGE_BASE
        from llama_index.core import Document
        for filename, text in KNOWLEDGE_BASE.items():
            if text.strip() and filename in ALLOWED_FILES:
                doc = Document(
                    text=text,
                    metadata={"file_name": filename, "source": filename}
                )
                documents.append(doc)

    if not documents:
        print("ERROR: No documents could be loaded!")
        return None
    
    print(f"[INFO] Total documents/pages loaded: {len(documents)}")
    
    # Step 1: Use a better node parser for technical tutorials
    from llama_index.core.node_parser import SentenceSplitter
    node_parser = SentenceSplitter(chunk_size=768, chunk_overlap=128) # Slightly larger chunks for SDLC context
    
    storage_context = StorageContext.from_defaults()
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        transformations=[node_parser],
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
    "You are the Kadel Lab Reasoning Assistant. Your goal is to provide logical, accurate, and context-backed answers.\n\n"
    "## REASONING PROTOCOL:\n"
    "1. Analyze the Question: Understand exactly what the user is asking.\n"
    "2. Consult Context: Look for relevant facts and rules in the provided documents.\n"
    "3. Logical Step-by-Step: If the question requires reasoning (type: logical), explain the logic behind the answer briefly.\n"
    "4. NO OUTSIDE INFO: Do not use information from your training data that is not in the context.\n"
    "5. NO HALLUCINATION: If the logic cannot be supported by the text, say \"I cannot provide a logical conclusion based on the available documents.\"\n\n"
    "## OUTPUT FORMAT:\n"
    "- DIRECT: No panygerics or fillers.\n"
    "- CLEAR: Use simple but professional language.\n"
    "- EVIDENCE-BASED: Mention the source if multiple documents are involved.\n\n"
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
    """Retrieves nodes with a multi-pass approach to ensure technical terms aren't missed."""
    # Pass 1: Broad semantic search
    retriever = index.as_retriever(similarity_top_k=25)
    raw_nodes = retriever.retrieve(query)
    
    if not raw_nodes:
        return []

    # Sort nodes: Prioritize the specific document if mentioned in query
    query_lower = query.lower()
    
    def get_priority(node):
        source = node.node.metadata.get('file_name', '').lower()
        content = node.node.get_content().lower()
        score = 0
        
        # Boost specific documents
        if "email" in query_lower and "email etiquette" in source: score += 50
        if "sdlc" in query_lower and "software" in source: score += 50
        if "policy" in query_lower and "policy" in source: score += 50
        
        # Severe penalty for irrelevant documents
        if "email" in query_lower and "software" in source and "email" not in content:
            score -= 100
        
        # Boost exact keywords
        if "do's" in query_lower and "do " in content: score += 5
        if "don'ts" in query_lower and "don't" in content: score += 5
        
        return score + (node.score or 0)

    # Filter out severely penalized nodes
    nodes_sorted = [n for n in raw_nodes if get_priority(n) > -50]
    nodes_sorted = sorted(nodes_sorted, key=get_priority, reverse=True)
    
    return nodes_sorted[:8] 

def build_smart_context(nodes: list, query: str) -> str:
    """Provides full relevant chunks with clear source markers to prevent data loss while keeping context manageable."""
    context_parts = []
    
    for i, node in enumerate(nodes):
        text = node.node.get_content() if hasattr(node.node, 'get_content') else node.node.text
        source = node.node.metadata.get('file_name', 'Unknown Source')
        if not text:
            continue
            
        clean_text = text.strip()
        context_parts.append(f"REFERENCE {i+1} [Source: {source}]:\n{clean_text}")
        
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
        
        # Language specific "Not found" messages
        not_found_msgs = {
            "English": "I could not find this information in the provided document.",
            "Hindi": "मुझे प्रदान किए गए दस्तावेज़ में यह जानकारी नहीं मिली।",
            "Hinglish": "Mujhe provided document mein yeh information nahi mili."
        }
        not_found_msg = not_found_msgs.get(manual_lang, not_found_msgs["English"])

        system_prompt = f"""You are the Kadel Labs Professional Assistant. 
Your only task is to extract precisely what the user asks for from the DOCUMENT CONTEXT below.

STRICT INSTRUCTIONS:
1. TABULAR FORMAT: If the user asks for a table or do's/don'ts, YOU MUST provide a Markdown table.
2. CATEGORIZATION: For Do's and Don'ts, categorize the rules by topic (e.g., Tone, Subject Line, Etiquette).
3. If the answer is in the document, PROVIDE IT. Do not say you can't find it if it is partially mentioned.
4. If information is totally absent, say: "{not_found_msg}".

LANGUAGE: {manual_lang}

DOCUMENT CONTEXT:
{context}"""

        user_query_msg = f"Question: {user_input}"

        # LOG PROMPT FOR DEBUGGING (Development only)
        with open("last_prompt.txt", "w", encoding="utf-8") as f:
            f.write("=== SYSTEM PROMPT ===\n")
            f.write(system_prompt)
            f.write("\n\n=== USER QUERY ===\n")
            f.write(user_query_msg)

        # Execute with only the last 2 interactions to keep focus sharp
        focused_history = history[-2:] if len(history) > 2 else history
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
            except Exception as e:
                error_str = str(e).lower()
                friendly_msg = "⚠️ An unexpected error occurred. Please try again."
                
                if "429" in error_str or "rate limit" in error_str:
                    friendly_msg = "🕒 The AI engine is currently busy (Rate Limit). Please wait a few seconds and try again."
                elif "503" in error_str or "overloaded" in error_str:
                    friendly_msg = "🌪️ The AI server is currently overloaded. Please try again in a moment."
                elif "authentication" in error_str or "401" in error_str:
                    friendly_msg = "🔑 AI Authentication failed. Please check the API configuration."
                
                print(f"DEBUG Error: {e}")
                yield json.dumps({"error": friendly_msg}) + "\n"
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
        error_str = str(e).lower()
        friendly_msg = "⚠️ An error occurred during response generation."
        if "429" in error_str or "rate limit" in error_str:
            friendly_msg = "🕒 The assistant is receiving too many requests. Please pause for a moment."
            
        yield f"\n\n{friendly_msg}"
