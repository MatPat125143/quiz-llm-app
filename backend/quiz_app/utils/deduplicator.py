import logging
import re
from enum import Enum
from typing import NamedTuple, Optional

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    MATH = "math"
    FACTUAL = "factual"
    DEFINITION = "definition"
    CONCEPT = "concept"


DEDUP_THRESHOLDS = {
    QuestionType.MATH: 0.97,
    QuestionType.FACTUAL: 0.92,
    QuestionType.DEFINITION: 0.90,
    QuestionType.CONCEPT: 0.93,
}

ANSWER_OVERLAP_THRESHOLD = 0.75
DEFAULT_THRESHOLD = 0.93


class DuplicateCheckResult(NamedTuple):
    is_duplicate: bool
    reason: str
    score: float


class UniversalDeduplicator:

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.lower()

        text = ' '.join(text.split())

        text = text.rstrip('.,!?:;')

        replacements = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l',
            'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        for pl, en in replacements.items():
            text = text.replace(pl, en)

        return text

    def detect_question_type(self, question_text: str) -> QuestionType:
        text_lower = question_text.lower()

        math_indicators = [
            r'\d+[\+\-\*/\^]\d+',
            r'√',
            r'pierwiastek',
            r'równanie',
            r'oblicz',
            r'wynik',
            r'suma',
            r'różnica',
            r'iloczyn',
            r'iloraz',
            r'\bx\b.*=',
        ]
        for pattern in math_indicators:
            if re.search(pattern, text_lower):
                return QuestionType.MATH

        factual_indicators = [
            r'\b\d{4}\b',
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

        return QuestionType.CONCEPT

    def extract_math_pattern(self, question_text: str) -> Optional[str]:

        math_expr = re.findall(r'[\d\w]+[\+\-\*/\^√()]+[\d\w]+(?:[\+\-\*/\^√()]+[\d\w]+)*', question_text)

        if not math_expr:
            return None

        patterns = []
        for expr in math_expr:
            pattern = re.sub(r'\d+', 'VAR', expr)
            patterns.append(pattern)

        return '|'.join(sorted(patterns))

    def calculate_answer_similarity(self, answers1: list, answers2: list) -> float:
        if not answers1 or not answers2:
            return 0.0

        set1 = {self.normalize_text(ans) for ans in answers1}
        set2 = {self.normalize_text(ans) for ans in answers2}

        set1.discard('')
        set2.discard('')

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def is_duplicate(
            self,
            new_question_text: str,
            new_answers: list,
            existing_question_text: str,
            existing_answers: list,
            semantic_similarity: float,
    ) -> DuplicateCheckResult:

        new_norm = self.normalize_text(new_question_text)
        existing_norm = self.normalize_text(existing_question_text)

        if new_norm == existing_norm:
            return DuplicateCheckResult(True, "exact_text_match", 1.0)

        new_type = self.detect_question_type(new_question_text)
        existing_type = self.detect_question_type(existing_question_text)

        if new_type == QuestionType.MATH and existing_type == QuestionType.MATH:

            new_pattern = self.extract_math_pattern(new_question_text)
            existing_pattern = self.extract_math_pattern(existing_question_text)

            if new_pattern and existing_pattern and new_pattern != existing_pattern:
                logger.debug(
                    "Math patterns differ: '%s' vs '%s' - not duplicate",
                    new_pattern,
                    existing_pattern,
                )
                return DuplicateCheckResult(False, "different_math_pattern", 0.0)

        answer_similarity = self.calculate_answer_similarity(new_answers, existing_answers)

        if answer_similarity > ANSWER_OVERLAP_THRESHOLD:
            logger.debug(
                "High answer overlap: %.2f - likely duplicate",
                answer_similarity
            )
            return DuplicateCheckResult(True, "high_answer_overlap", answer_similarity)

        threshold = DEDUP_THRESHOLDS.get(new_type, DEFAULT_THRESHOLD)

        if semantic_similarity > threshold:
            return DuplicateCheckResult(
                True,
                f"high_semantic_similarity_{new_type.value}",
                semantic_similarity
            )

        return DuplicateCheckResult(False, "not_duplicate", semantic_similarity)

    def get_adaptive_threshold(self, question_text: str) -> float:
        q_type = self.detect_question_type(question_text)
        return DEDUP_THRESHOLDS.get(q_type, DEFAULT_THRESHOLD)
