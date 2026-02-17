import json
import logging
import re
import unicodedata
from openai import OpenAI, OpenAIError
from .config import LLMConfig
from .prompts import QuizPrompts

logger = logging.getLogger(__name__)


class QuestionGenerator:

    def __init__(self):
        self.client = None

        if not LLMConfig.is_openai_available():
            logger.warning("OPENAI_API_KEY not set - question generation disabled")
            return

        try:
            self.client = OpenAI(api_key=LLMConfig.OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.warning("openai package not installed - question generation disabled")
        except (OpenAIError, ValueError, TypeError) as e:
            logger.error(f"Failed to initialize OpenAI: {e}")

    def generate_multiple_questions(
            self,
            topic,
            difficulty,
            count,
            subtopic=None,
            knowledge_level='high_school',
            existing_questions=None,
    ):

        difficulty_text = self._normalize_difficulty(difficulty)

        if self.client is None:
            raise RuntimeError("Question generation unavailable: OpenAI client not initialized")

        try:
            context_msg = (
                f" (with context of {len(existing_questions)} existing)"
                if existing_questions
                else ""
            )
            logger.info(
                "Generating %s diverse AI questions for topic: %s, subtopic: %s, "
                "knowledge: %s, difficulty: %s%s",
                count,
                topic,
                subtopic,
                knowledge_level,
                difficulty_text,
                context_msg,
            )
            try:
                return self._generate_multiple_ai_questions(
                    topic,
                    difficulty_text,
                    count,
                    subtopic,
                    knowledge_level,
                    existing_questions,
                )
            except ValueError as e:
                if "No valid questions returned by model" not in str(e):
                    raise

                logger.warning(
                    "Batch generation returned 0 valid questions; "
                    "falling back to single-question generation"
                )
                return self._generate_multiple_with_single_fallback(
                    topic=topic,
                    difficulty_text=difficulty_text,
                    count=count,
                    subtopic=subtopic,
                    knowledge_level=knowledge_level,
                    existing_questions=existing_questions,
                )
        except (OpenAIError, json.JSONDecodeError, ValueError, TypeError, KeyError, IndexError) as e:
            logger.error(f"Error generating multiple AI questions: {e}")
            raise

    def generate_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):

        difficulty_text = self._normalize_difficulty(difficulty)

        if self.client is None:
            raise RuntimeError("Question generation unavailable: OpenAI client not initialized")

        try:
            logger.info(
                "Generating AI question for topic: %s, subtopic: %s, knowledge: %s, difficulty: %s",
                topic,
                subtopic,
                knowledge_level,
                difficulty_text,
            )
            return self._generate_ai_question(topic, difficulty_text, subtopic, knowledge_level)
        except (OpenAIError, json.JSONDecodeError, ValueError, TypeError, KeyError, IndexError) as e:
            logger.error(f"Error generating AI question: {e}")
            raise

    def _normalize_difficulty(self, difficulty):
        if isinstance(difficulty, (int, float)):
            from .difficulty_adapter import DifficultyAdapter
            adapter = DifficultyAdapter()
            return adapter.get_difficulty_level(difficulty)
        return difficulty

    def _generate_multiple_ai_questions(
            self,
            topic,
            difficulty,
            count,
            subtopic=None,
            knowledge_level='high_school',
            existing_questions=None,
    ):
        user_prompt = QuizPrompts.build_multiple_questions_prompt(
            topic, difficulty, count, subtopic, knowledge_level, existing_questions
        )

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": QuizPrompts.SYSTEM_PROMPT_DIVERSE},
                {"role": "user", "content": user_prompt}
            ],
            **LLMConfig.get_openai_params_multiple()
        )

        content = response.choices[0].message.content.strip()
        content = self._clean_json_response(content)
        questions_data = json.loads(content)

        questions_data = self._validate_multiple_questions(questions_data, count)

        logger.info(
            "Generated %s diverse AI questions successfully",
            len(questions_data),
        )
        return questions_data

    def _generate_ai_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        user_prompt = QuizPrompts.build_single_question_prompt(
            topic, difficulty, subtopic, knowledge_level
        )

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": QuizPrompts.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            **LLMConfig.get_openai_params_single()
        )

        content = response.choices[0].message.content.strip()
        content = self._clean_json_response(content)
        question_data = json.loads(content)

        self._validate_single_question(question_data)

        logger.info("AI question generated successfully")
        return question_data

    def _clean_json_response(self, content):
        content = content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "```", 1)
        if "```" in content:
            parts = [p for p in content.split("```") if p.strip()]
            if parts:
                content = parts[0].strip()
        decoder = json.JSONDecoder()
        for idx, ch in enumerate(content):
            if ch in "{[":
                try:
                    _, end = decoder.raw_decode(content[idx:])
                    return content[idx:idx + end].strip()
                except json.JSONDecodeError:
                    continue
        return content.strip()

    def _validate_single_question(self, question_data):
        required_keys = [
            "question",
            "correct_answer",
            "wrong_answers",
            "explanation",
        ]
        if not all(key in question_data for key in required_keys):
            raise ValueError(f"Missing required keys in response. Got: {question_data.keys()}")

        question_text = question_data["question"]
        if not isinstance(question_text, str) or len(question_text.strip()) < 8:
            raise ValueError("Question text must be a non-empty string")

        if self._looks_like_binary_question(question_text):
            raise ValueError("Question appears to be binary/50-50 and was rejected")

        correct_answer = question_data["correct_answer"]
        if not isinstance(correct_answer, str) or not correct_answer.strip():
            raise ValueError("correct_answer must be a non-empty string")

        explanation = question_data["explanation"]
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("explanation must be a non-empty string")

        if not isinstance(question_data["wrong_answers"], list):
            raise ValueError("wrong_answers must be a list")

        if len(question_data["wrong_answers"]) != 3:
            raise ValueError(
                f"Expected 3 wrong answers, got {len(question_data['wrong_answers'])}"
            )

        wrong_answers = question_data["wrong_answers"]
        if not all(isinstance(ans, str) and ans.strip() for ans in wrong_answers):
            raise ValueError("All wrong answers must be non-empty strings")

        normalized_answers = [
            self._normalize_answer_text(correct_answer),
            *[self._normalize_answer_text(ans) for ans in wrong_answers],
        ]
        if len(set(normalized_answers)) != 4:
            raise ValueError("Answers must contain 4 unique options")

        if self._contains_forbidden_option_text([correct_answer, *wrong_answers]):
            raise ValueError("Answers contain forbidden option patterns")

        if not self._explanation_mentions_answer(explanation, correct_answer):
            raise ValueError("Explanation must explicitly include the correct answer")

        if self._is_likely_math_question(question_text):
            if self._is_ambiguous_numeric_question(question_text, correct_answer):
                raise ValueError("Numeric question is ambiguous (likely missing rounding instruction)")
            self._validate_basic_math_consistency(question_text, correct_answer)

    def _validate_multiple_questions(self, questions_data, expected_count):
        if not isinstance(questions_data, list):
            raise ValueError(
                f"Expected list of questions, got: {type(questions_data)}"
            )

        if len(questions_data) != expected_count:
            logger.warning(f"Requested {expected_count} questions but got {len(questions_data)}")

        valid_questions = []
        for i, q_data in enumerate(questions_data):
            try:
                self._validate_single_question(q_data)
                valid_questions.append(q_data)
            except ValueError as e:
                logger.warning("Rejected malformed question #%s: %s", i + 1, e)

        if not valid_questions:
            raise ValueError("No valid questions returned by model")

        return valid_questions

    def _generate_multiple_with_single_fallback(
        self,
        topic,
        difficulty_text,
        count,
        subtopic=None,
        knowledge_level='high_school',
        existing_questions=None,
    ):
        target = max(1, int(count))
        max_attempts = max(target * 4, target + 3)
        attempts = 0
        generated = []

        existing_keys = {
            self._normalize_question_text(text)
            for text in (existing_questions or [])
            if isinstance(text, str) and text.strip()
        }
        local_keys = set()

        while len(generated) < target and attempts < max_attempts:
            attempts += 1
            try:
                question_data = self._generate_ai_question(
                    topic=topic,
                    difficulty=difficulty_text,
                    subtopic=subtopic,
                    knowledge_level=knowledge_level,
                )
            except (OpenAIError, json.JSONDecodeError, ValueError, TypeError, KeyError, IndexError) as e:
                logger.warning(
                    "Fallback generation attempt %s/%s rejected: %s",
                    attempts,
                    max_attempts,
                    e,
                )
                continue

            question_key = self._normalize_question_text(question_data.get("question"))
            if question_key in existing_keys or question_key in local_keys:
                logger.warning(
                    "Fallback generation attempt %s/%s skipped duplicate question text",
                    attempts,
                    max_attempts,
                )
                continue

            local_keys.add(question_key)
            generated.append(question_data)

        if not generated:
            raise ValueError("No valid questions returned by model")

        if len(generated) < target:
            logger.warning(
                "Fallback generated %s/%s valid questions after %s attempts",
                len(generated),
                target,
                attempts,
            )
        else:
            logger.info(
                "Fallback generated %s valid questions in %s attempts",
                len(generated),
                attempts,
            )

        return generated

    def _normalize_answer_text(self, value):
        text = (value or "").strip().lower()
        text = " ".join(text.split())
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def _normalize_question_text(self, value):
        return self._normalize_answer_text(value)

    def _contains_forbidden_option_text(self, options):
        forbidden_patterns = [
            r"\bwszystkie\b.{0,20}\bpowyzsze\b",
            r"\bzadna\b.{0,20}\bpowyzszych\b",
            r"\bobie\b.{0,20}\bodpowiedzi\b",
            r"\b(a|b|c|d)\s*i\s*(a|b|c|d)\b",
            r"\bnie\s+wiem\b",
        ]

        for option in options:
            normalized = (option or "").strip().lower()
            normalized = unicodedata.normalize("NFKD", normalized)
            normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
            normalized = " ".join(normalized.split())
            if any(re.search(pattern, normalized) for pattern in forbidden_patterns):
                return True
        return False

    def _looks_like_binary_question(self, question_text):
        q = (question_text or "").strip().lower()
        q = unicodedata.normalize("NFKD", q)
        q = "".join(ch for ch in q if not unicodedata.combining(ch))
        q = " ".join(q.split())

        blocked_patterns = [
            r"\b50\s*/\s*50\b",
            r"\bprawda\s*/\s*falsz\b",
            r"\bprawda\s+czy\s+falsz\b",
            r"\btak\s*/\s*nie\b",
            r"\btak\s+czy\s+nie\b",
            r"\bwybierz\b.{0,20}\bz\s*(2|3)\b",
            r"\bktora\b.{0,35}\b(wieksza|mniejsza)\b.{0,40}\bczy\b",
            r"\bktora\b.{0,20}\bliczba\b.{0,35}\b(wieksza|mniejsza)\b",
            r"\b(wieksza|mniejsza)\b.{0,25}\bliczba\b",
            r"\bporownaj\b.{0,30}\bliczb",
            r"\b(wskaz|wybierz)\b.{0,30}\b(wieksza|mniejsza)\b.{0,30}\bliczb",
            r"\bczy\b.{0,25}\b(wieksza|mniejsza)\b",
        ]

        return any(re.search(pattern, q) for pattern in blocked_patterns)

    def _explanation_mentions_answer(self, explanation, correct_answer):
        normalized_expl = self._normalize_answer_text(explanation)
        normalized_answer = self._normalize_answer_text(correct_answer)
        return bool(normalized_answer) and normalized_answer in normalized_expl

    def _parse_numeric_answer(self, value):
        token = (value or "").strip().replace(" ", "").replace(",", ".")
        if re.fullmatch(r"-?\d+(\.\d+)?", token):
            return token
        return None

    def _is_ambiguous_numeric_question(self, question_text, correct_answer):
        numeric_answer = self._parse_numeric_answer(correct_answer)
        if not numeric_answer or "." not in numeric_answer:
            return False

        q = (question_text or "").strip().lower()
        q = unicodedata.normalize("NFKD", q)
        q = "".join(ch for ch in q if not unicodedata.combining(ch))
        q = " ".join(q.split())

        has_rounding_hint = any(
            token in q for token in ("zaokragl", "w przyblizeniu", "przybliz", "do miejsca")
        )
        if has_rounding_hint:
            return False

        decimal_places = len(numeric_answer.split(".", 1)[1])
        has_risky_operation = any(token in q for token in ("pierwiastek", "/", "podziel", "iloraz", ":"))

        return has_risky_operation and decimal_places > 2

    def _is_likely_math_question(self, question_text):
        q = (question_text or "").strip().lower()
        q = unicodedata.normalize("NFKD", q)
        q = "".join(ch for ch in q if not unicodedata.combining(ch))
        q = " ".join(q.split())

        math_keywords = (
            "oblicz",
            "rownanie",
            "pierwiastek",
            "iloraz",
            "suma",
            "roznica",
            "procent",
            "dzialanie",
        )
        if any(token in q for token in math_keywords):
            return True

        if re.search(r"-?\d+(?:\.\d+)?\s*[\+\-\*/\^]\s*-?\d+(?:\.\d+)?", q):
            return True
        if re.search(r"-?\d+(?:\.\d+)?\s*[a-z]\s*=\s*-?\d+(?:\.\d+)?", q):
            return True

        return False

    def _validate_basic_math_consistency(self, question_text, correct_answer):
        normalized_q = (question_text or "").strip().lower()
        normalized_q = unicodedata.normalize("NFKD", normalized_q)
        normalized_q = "".join(ch for ch in normalized_q if not unicodedata.combining(ch))
        normalized_q = normalized_q.replace("×", "*").replace("x", "*").replace(":", "/")
        normalized_q = " ".join(normalized_q.split())

        answer_token = self._parse_numeric_answer(correct_answer)
        if answer_token is None:
            return
        answer_value = float(answer_token)

        expected = self._extract_expected_for_linear_equation(normalized_q)
        if expected is None:
            expected = self._extract_expected_for_basic_operation(normalized_q)
        if expected is None:
            return

        if abs(expected - answer_value) > 1e-6:
            raise ValueError("Correct answer does not match the arithmetic result in question")

    def _extract_expected_for_linear_equation(self, normalized_q):
        if "rownanie" not in normalized_q:
            return None

        match = re.search(r"(-?\d+(?:\.\d+)?)\s*([a-z])\s*=\s*(-?\d+(?:\.\d+)?)", normalized_q)
        if not match:
            return None

        a = float(match.group(1))
        b = float(match.group(3))
        if a == 0:
            return None
        return b / a

    def _extract_expected_for_basic_operation(self, normalized_q):
        if not any(token in normalized_q for token in ("oblicz", "ile wynosi", "wynik", "rozwiaz")):
            return None

        expressions = re.findall(
            r"(?=(-?\d+(?:\.\d+)?\s*[\+\-\*/\^]\s*-?\d+(?:\.\d+)?))",
            normalized_q
        )
        if len(expressions) != 1:
            return None

        expr = expressions[0]
        match = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([\+\-\*/\^])\s*(-?\d+(?:\.\d+)?)", expr)
        if not match:
            return None

        left = float(match.group(1))
        operator = match.group(2)
        right = float(match.group(3))

        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                return None
            return left / right
        if operator == "^":
            return left ** right
        return None
