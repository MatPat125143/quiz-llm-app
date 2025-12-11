"""
Universal question deduplication system that works for ALL question types.
Handles math, history, geography, definitions, concepts, etc.
"""
import logging
import re
from enum import Enum
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of questions the system can detect"""
    MATH = "math"
    FACTUAL = "factual"  # Dates, events, names
    DEFINITION = "definition"  # What is X?
    CONCEPT = "concept"  # General knowledge


class UniversalDeduplicator:
    """
    Multi-level deduplication that adapts to question type.
    Works for ALL subjects: math, history, geography, biology, etc.
    """

    def __init__(self):
        # Type-specific similarity thresholds
        self.thresholds = {
            QuestionType.MATH: 0.97,       # Math can have similar words but different formulas
            QuestionType.FACTUAL: 0.92,     # Dates/events need more strictness
            QuestionType.DEFINITION: 0.90,  # Definitions can be phrased differently
            QuestionType.CONCEPT: 0.93      # General knowledge
        }

    def normalize_text(self, text: str) -> str:
        """
        Universal text normalization for ALL question types.
        Removes formatting differences while preserving meaning.
        """
        if not text:
            return ""

        # Lowercase
        text = text.lower()

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove punctuation at end (but keep internal punctuation for math/formulas)
        text = text.rstrip('.,!?:;')

        # Normalize Polish characters variants
        replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l',
            'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        for pl, en in replacements.items():
            text = text.replace(pl, en)

        return text

    def detect_question_type(self, question_text: str) -> QuestionType:
        """
        Detects question type to apply appropriate deduplication rules.
        Works for ALL subjects.
        """
        text_lower = question_text.lower()

        # MATH: Contains mathematical operators, numbers, formulas
        math_indicators = [
            r'\d+[\+\-\*/\^]\d+',  # 2+3, 5*7, 2^4
            r'√',  # Square root
            r'pierwiastek',
            r'równanie',
            r'oblicz',
            r'wynik',
            r'suma',
            r'różnica',
            r'iloczyn',
            r'iloraz',
            r'\bx\b.*=',  # Equations with x
        ]
        for pattern in math_indicators:
            if re.search(pattern, text_lower):
                return QuestionType.MATH

        # FACTUAL: Dates, years, specific events, names
        factual_indicators = [
            r'\b\d{4}\b',  # Years like 1918, 2020
            r'w którym roku',
            r'kiedy',
            r'kto',
            r'gdzie',
            r'data',
            r'wydarzył',
            r'odkrył',
            r'wynalazł',
        ]
        for pattern in factual_indicators:
            if re.search(pattern, text_lower):
                return QuestionType.FACTUAL

        # DEFINITION: What is X? Define X. Meaning of X.
        definition_indicators = [
            r'^(co to jest|co to|czym jest)',
            r'definicja',
            r'znaczenie',
            r'oznacza',
            r'definiuje się',
        ]
        for pattern in definition_indicators:
            if re.search(pattern, text_lower):
                return QuestionType.DEFINITION

        # Default: CONCEPT (general knowledge)
        return QuestionType.CONCEPT

    def extract_math_pattern(self, question_text: str) -> Optional[str]:
        """
        Extracts mathematical pattern from question.
        Different patterns = different questions (even if similar words).

        Examples:
        - "2^4 + 3" → pattern: "VAR^VAR+VAR"
        - "3^2 + 4*5" → pattern: "VAR^VAR+VAR*VAR"
        These are DIFFERENT patterns → different questions!
        """
        # Find all mathematical expressions
        # Match: numbers, operators, variables, parentheses
        math_expr = re.findall(r'[\d\w]+[\+\-\*/\^√()]+[\d\w]+(?:[\+\-\*/\^√()]+[\d\w]+)*', question_text)

        if not math_expr:
            return None

        # Convert to pattern by replacing numbers with VAR
        patterns = []
        for expr in math_expr:
            # Replace all numbers with VAR to get structure
            pattern = re.sub(r'\d+', 'VAR', expr)
            patterns.append(pattern)

        return '|'.join(sorted(patterns))

    def calculate_answer_similarity(self, answers1: list, answers2: list) -> float:
        """
        Calculates Jaccard similarity between answer sets.
        Works for ALL question types.

        High similarity → likely duplicate question
        Low similarity → different questions
        """
        if not answers1 or not answers2:
            return 0.0

        # Normalize all answers
        set1 = {self.normalize_text(ans) for ans in answers1}
        set2 = {self.normalize_text(ans) for ans in answers2}

        # Remove empty strings
        set1.discard('')
        set2.discard('')

        if not set1 or not set2:
            return 0.0

        # Jaccard similarity
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def is_duplicate(
        self,
        new_question_text: str,
        new_answers: list,
        existing_question_text: str,
        existing_answers: list,
        semantic_similarity: float
    ) -> Tuple[bool, str, float]:
        """
        Multi-level duplicate detection that works for ALL question types.

        Returns:
            (is_duplicate, reason, confidence)
        """

        # LEVEL 1: Exact text match (normalized)
        new_norm = self.normalize_text(new_question_text)
        existing_norm = self.normalize_text(existing_question_text)

        if new_norm == existing_norm:
            return True, "exact_text_match", 1.0

        # LEVEL 2: Question type detection
        new_type = self.detect_question_type(new_question_text)
        existing_type = self.detect_question_type(existing_question_text)

        # LEVEL 3: Type-specific checks
        if new_type == QuestionType.MATH and existing_type == QuestionType.MATH:
            # For MATH questions: check if patterns are different
            new_pattern = self.extract_math_pattern(new_question_text)
            existing_pattern = self.extract_math_pattern(existing_question_text)

            if new_pattern and existing_pattern and new_pattern != existing_pattern:
                # Different math patterns → definitely different questions
                logger.debug(f"Math patterns differ: '{new_pattern}' vs '{existing_pattern}' - not duplicate")
                return False, "different_math_pattern", 0.0

        # LEVEL 4: Answer similarity check (works for ALL types)
        answer_similarity = self.calculate_answer_similarity(new_answers, existing_answers)

        if answer_similarity > 0.75:
            # High answer overlap suggests duplicate (all types)
            logger.debug(f"High answer overlap: {answer_similarity:.2f} - likely duplicate")
            return True, "high_answer_overlap", answer_similarity

        # LEVEL 5: Semantic similarity with type-specific thresholds
        threshold = self.thresholds.get(new_type, 0.93)

        if semantic_similarity > threshold:
            return True, f"high_semantic_similarity_{new_type.value}", semantic_similarity

        # Not a duplicate
        return False, "not_duplicate", semantic_similarity

    def get_adaptive_threshold(self, question_text: str) -> float:
        """
        Returns adaptive similarity threshold based on question type.
        Used for database search optimization.
        """
        q_type = self.detect_question_type(question_text)
        return self.thresholds.get(q_type, 0.93)
