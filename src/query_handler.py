import os
# import spacy
from spellchecker import SpellChecker
from groq import Groq
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Simple Stopwords for fallback
STOPWORDS = {"is", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by", "from", "of", "about", "as"}

SIMPLE_GREETINGS = [
    "hello", "hi", "hey", "good morning", 
    "good afternoon", "how are you", "what can you do",
    "help", "who are you", "namaste", "hi there", "hello there"
]

spell = SpellChecker()

class QueryHandler:
    @staticmethod
    def detect_question_type(query: str) -> dict:
        query_lower = query.lower().strip()
        
        # Date questions
        if any(w in query_lower for w in ["start date", "end date", "when", "date", "deadline", "duration", "period", "from", "till"]):
            return {
                "type": "date", 
                "instruction": "Give only the date or date range. Example: '16-Feb-2026'"
            }
        
        # Count/number questions  
        elif any(w in query_lower for w in ["how many", "count", "number of", "total", "how much"]):
            return {
                "type": "count",
                "instruction": "Give only the number with brief context. Example: 'There are 7 Data Ethics Principles.'"
            }
        
        # Yes/No questions
        elif any(w in query_lower for w in ["can", "is", "are", "does", "do", "will", "should", "allowed", "permitted"]):
            return {
                "type": "yesno",
                "instruction": "Start with Yes or No, then explain in maximum 2 sentences."
            }
        
        # Definition questions
        elif any(w in query_lower for w in ["what is", "what are", "define", "explain", "describe", "meaning of"]):
            return {
                "type": "definition",
                "instruction": "Give a clear definition in 2-3 sentences maximum."
            }
        
        # List questions
        elif any(w in query_lower for w in ["list", "mention", "enumerate", "what all", "types of", "kinds of"]):
            return {
                "type": "list",
                "instruction": "Give a numbered or bullet list. Keep each point brief."
            }
        
        # Name/person questions
        elif any(w in query_lower for w in ["who", "name", "person", "employee", "trainee"]):
            return {
                "type": "name",
                "instruction": "Give only the name and their role. One sentence."
            }
        
        # Policy/rule questions
        elif any(w in query_lower for w in ["policy", "rule", "guideline", "procedure", "notice period", "termination", "confidential"]):
            return {
                "type": "policy",
                "instruction": "Summarize the policy in 3-4 sentences. No legal jargon copying."
            }
        
        # Default
        else:
            return {
                "type": "general",
                "instruction": "Answer directly and concisely in maximum 3 sentences."
            }

    @staticmethod
    def detect_intent(query: str) -> str:
        query_lower = query.lower().strip()
        words = query_lower.split()
        
        # Check greeting with exact word matching
        if any(g in words for g in SIMPLE_GREETINGS) or any(g == query_lower for g in SIMPLE_GREETINGS):
            return "greeting"
        
        # Check very short query (likely needs clarification or expansion)
        if len(words) < 3 and query_lower not in ["posh", "ethics", "contract"]:
            return "short_query"
        
        # Normal RAG query
        return "rag"

    @staticmethod
    def handle_greeting(query: str) -> str:
        greetings_responses = {
            "hello": "Hello! I am the Kadel Lab Training Assistant. I can help you with course information, schedules, policies, and fees. What would you like to know?",
            "hi": "Hi there! How can I help you with your training center queries today?",
            "how are you": "I am working well and ready to help! Ask me anything about courses, schedules, or training policies.",
            "what can you do": "I can answer questions about: courses available, training schedules, fees, attendance policies, trainee guidelines, and contract details. Just ask!",
            "who are you": "I am the Kadel Lab Training Center Assistant, powered by AI. I answer questions based on official training documents.",
            "help": "I can help with: course information, training schedules, fees and payments, attendance policies, contract details, and trainee guidelines.",
            "namaste": "Namaste! Main Kadel Lab assistant hoon. Main aapki kya sahayata kar sakta hoon?"
        }
        
        query_lower = query.lower().strip()
        for key, response in greetings_responses.items():
            if key in query_lower:
                return response
        
        return "Hello! I am the Training Center Assistant. How can I help you today?"

    @staticmethod
    def spell_check(query: str) -> str:
        words = query.split()
        corrected_words = []
        for word in words:
            misspelled = spell.unknown([word])
            if misspelled:
                correction = spell.correction(word)
                corrected_words.append(correction if correction else word)
            else:
                corrected_words.append(word)
        return " ".join(corrected_words)

    @staticmethod
    def extract_keywords(query: str) -> str:
        words = query.lower().split()
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
        return " ".join(list(set(keywords)))

    @staticmethod
    def expand_query(query: str) -> str:
        """Expand query with synonyms for document matching."""
        q = query.lower()
        if any(w in q for w in ["location", "office", "address", "city", "place"]):
            return f"{query} address office location Bangalore Hoodi Junction city"
        if any(w in q for w in ["stipend", "salary", "pay", "fees", "money"]):
            return f"{query} stipend salary payment amount rupees"
        if any(w in q for w in ["date", "start", "end", "period", "duration"]):
            return f"{query} date start 2026 duration months"
        return query

    @classmethod
    def process(cls, query: str, provider: str = "groq") -> dict:
        intent = cls.detect_intent(query)
        
        if intent == "greeting":
            return {"intent": "greeting", "response": cls.handle_greeting(query)}
            
        corrected = cls.spell_check(query)
        
        if intent == "short_query" or intent == "rag":
            corrected = cls.expand_query(corrected)
            
        keywords = cls.extract_keywords(corrected)
        q_type = cls.detect_question_type(corrected)
        
        return {
            "intent": intent,
            "type_info": q_type,
            "original": query,
            "corrected": corrected,
            "keywords": keywords
        }
