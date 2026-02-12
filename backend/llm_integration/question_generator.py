import json
import logging
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
            return self._generate_multiple_ai_questions(
                topic,
                difficulty_text,
                count,
                subtopic,
                knowledge_level,
                existing_questions,
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

        self._validate_multiple_questions(questions_data, count)

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

        if not isinstance(question_data["wrong_answers"], list):
            raise ValueError("wrong_answers must be a list")

        if len(question_data["wrong_answers"]) != 3:
            raise ValueError(
                f"Expected 3 wrong answers, got {len(question_data['wrong_answers'])}"
            )

    def _validate_multiple_questions(self, questions_data, expected_count):
        if not isinstance(questions_data, list):
            raise ValueError(
                f"Expected list of questions, got: {type(questions_data)}"
            )

        if len(questions_data) != expected_count:
            logger.warning(f"Requested {expected_count} questions but got {len(questions_data)}")

        for i, q_data in enumerate(questions_data):
            self._validate_single_question(q_data)
