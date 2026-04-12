import os
from groq import Groq as GroqClient
from llama_index.llms.gemini import Gemini
from dotenv import load_dotenv

load_dotenv()

# Step 1: Initialize direct Groq Client
groq_client = GroqClient(
    api_key=os.environ.get("GROQ_API_KEY")
)

class LLMManager:
    @staticmethod
    def call_groq_direct(system_prompt: str, user_query: str) -> str:
        """Calls Groq directly using the SDK (bypasses LlamaIndex to avoid stop sequence errors)."""
        try:
            response = groq_client.chat.completions.create(
                model=os.environ.get("GROQ_MODEL", "llama3-70b-8192"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=1024
                # NO stop parameter used here
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[GROQ ERROR FULL]: {e}")
            raise e

    @staticmethod
    def get_gemini_llm():
        """Returns LlamaIndex Gemini LLM (works fine with wrapper)."""
        return Gemini(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash"),
            temperature=0.1
        )

    @classmethod
    def query_with_fallback(cls, query_engine, user_query, provider="groq"):
        """Main entry point for queries with provider logic and error-based fallback."""
        if provider.lower() == "groq":
            try:
                # Step 1: Retrieve context manually
                retriever = query_engine.retriever
                nodes = retriever.retrieve(user_query)
                context = "\n\n".join([node.node.get_content() for node in nodes])
                
                # Step 2: Build strict system prompt
                system_prompt = f"""You are a strict document-based assistant for Kadel Labs.

STRICT RULES:
1. Answer ONLY from the document content provided below.
2. Read ALL pages of the document carefully before answering.
3. If answer exists in document → give SHORT and DIRECT answer only.
4. If answer is NOT in document → say only: "This information is not mentioned in the provided document." Nothing else.
5. NEVER say "Contact HR", "Refer to intranet", "Speak with manager".
6. NEVER refer to any outside source or document.
7. NEVER hallucinate or guess.

RESPONSE FORMAT:
- Yes/No question → "Yes/No. [1 line reason from document]"
- Date/Number → just the value
- Policy question → 2-3 lines max, only from document
- Not in document → "This information is not mentioned in the provided document."

CONTEXT:
{context}
"""
                # Step 3: Call Groq directly
                answer = cls.call_groq_direct(system_prompt, user_query)
                
                # Format sources for consistency
                sources = list(set([node.node.metadata.get("file_name", "unknown") for node in nodes]))
                source_text = "\n\n**Sources:** " + ", ".join(sources) if sources else ""
                
                return answer + source_text
                
            except Exception as e:
                print(f"Groq workflow failed: {e} — falling back to Gemini")
                # Fallback to Gemini via LlamaIndex wrapper
                return query_engine.query(user_query)
        else:
            # Gemini path - use LlamaIndex as is
            return query_engine.query(user_query)
