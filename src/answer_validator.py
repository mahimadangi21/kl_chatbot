import logging
import os

# Setup logging for low confidence queries
logging.basicConfig(
    filename='low_confidence.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

class AnswerValidator:
    @staticmethod
    def calculate_confidence(retrieved_nodes) -> float:
        if not retrieved_nodes:
            return 0.0
        # Get the highest similarity score
        scores = [node.score for node in retrieved_nodes if node.score is not None]
        return max(scores) if scores else 0.0

    @staticmethod
    def validate_answer(answer: str, retrieved_context: str) -> bool:
        # Check 1: Length
        if len(answer.strip()) < 20:
            return False
            
        # Check 2: Word overlap with context
        # Simple overlap check
        answer_words = set(answer.lower().split())
        context_words = set(retrieved_context.lower().split())
        
        # Remove common short words for a better check
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'with', 'is', 'are', 'was', 'were'}
        answer_keywords = {w for w in answer_words if len(w) > 3 and w not in stop_words}
        
        overlap = answer_keywords.intersection(context_words)
        
        # If no significant overlap, flag as potential hallucination
        if len(overlap) == 0 and len(answer_keywords) > 5:
            return False
            
        return True

    @staticmethod
    def log_low_confidence(query: str, score: float):
        logging.info(f"Low Confidence Query: {query} | Score: {score:.4f}")
