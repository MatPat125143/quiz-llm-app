"""
Generator pytań quizowych używający OpenAI API
"""
import json
import logging
import random
from openai import OpenAI
from .config import LLMConfig
from .prompts import QuizPrompts

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Klasa do generowania pytań quizowych"""

    def __init__(self):
        """Inicjalizacja generatora pytań"""
        self.client = None

        # Sprawdź czy klucz API jest ustawiony
        if not LLMConfig.is_openai_available():
            logger.warning("OPENAI_API_KEY not set - using fallback questions")
            return

        # Inicjalizuj klienta OpenAI
        try:
            self.client = OpenAI(api_key=LLMConfig.OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.warning("openai package not installed - using fallback questions")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")

    def generate_multiple_questions(self, topic, difficulty, count, subtopic=None, knowledge_level='high_school', existing_questions=None):
        """
        Generuje wiele RÓŻNORODNYCH pytań na raz z kontekstem pamięci.

        Args:
            topic (str): Temat pytań
            difficulty (float lub str): Poziom trudności 1-10 LUB 'łatwy'/'średni'/'trudny'
            count (int): Ile pytań wygenerować
            subtopic (str): Podtemat - opcjonalnie
            knowledge_level (str): Poziom wiedzy
            existing_questions (list): Lista już zadanych pytań w tej sesji (dla kontekstu)

        Returns:
            list: Lista słowników z pytaniami
        """
        # Konwertuj numeryczny poziom na tekstowy jeśli potrzeba
        difficulty_text = self._normalize_difficulty(difficulty)

        # Jeśli brak klienta OpenAI, użyj fallback
        if self.client is None:
            logger.info(f"Generating {count} fallback questions for topic: {topic}, difficulty: {difficulty_text}")
            return [self._generate_fallback_question(topic, difficulty_text) for _ in range(count)]

        # Generuj pytania używając OpenAI
        try:
            context_msg = f" (with context of {len(existing_questions)} existing)" if existing_questions else ""
            logger.info(f"Generating {count} diverse AI questions for topic: {topic}, subtopic: {subtopic}, knowledge: {knowledge_level}, difficulty: {difficulty_text}{context_msg}")
            return self._generate_multiple_ai_questions(topic, difficulty_text, count, subtopic, knowledge_level, existing_questions)
        except Exception as e:
            logger.error(f"Error generating multiple AI questions: {e}")
            logger.info("Falling back to predefined questions")
            return [self._generate_fallback_question(topic, difficulty_text) for _ in range(count)]

    def generate_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        """
        Generuje pytanie quizowe

        Args:
            topic (str): Temat pytania
            difficulty (float lub str): Poziom trudności 1-10 LUB 'łatwy'/'średni'/'trudny'
            subtopic (str): Podtemat - opcjonalnie
            knowledge_level (str): Poziom wiedzy

        Returns:
            dict: Słownik z pytaniem, odpowiedziami i wyjaśnieniem
        """
        # Konwertuj numeryczny poziom na tekstowy jeśli potrzeba
        difficulty_text = self._normalize_difficulty(difficulty)

        # Jeśli brak klienta OpenAI, użyj fallback
        if self.client is None:
            logger.info(f"Generating fallback question for topic: {topic}, difficulty: {difficulty_text}")
            return self._generate_fallback_question(topic, difficulty_text)

        # Generuj pytanie używając OpenAI
        try:
            logger.info(f"Generating AI question for topic: {topic}, subtopic: {subtopic}, knowledge: {knowledge_level}, difficulty: {difficulty_text}")
            return self._generate_ai_question(topic, difficulty_text, subtopic, knowledge_level)
        except Exception as e:
            logger.error(f"Error generating AI question: {e}")
            logger.info("Falling back to predefined questions")
            return self._generate_fallback_question(topic, difficulty_text)

    def _normalize_difficulty(self, difficulty):
        """Konwertuje numeryczny poziom trudności na tekstowy"""
        if isinstance(difficulty, (int, float)):
            from .difficulty_adapter import DifficultyAdapter
            adapter = DifficultyAdapter()
            return adapter.get_difficulty_level(difficulty)
        return difficulty

    def _generate_multiple_ai_questions(self, topic, difficulty, count, subtopic=None, knowledge_level='high_school', existing_questions=None):
        """Generuje wiele różnorodnych pytań używając OpenAI API z kontekstem pamięci"""
        user_prompt = QuizPrompts.build_multiple_questions_prompt(
            topic, difficulty, count, subtopic, knowledge_level, existing_questions
        )

        # Wywołaj OpenAI API
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": QuizPrompts.SYSTEM_PROMPT_DIVERSE},
                {"role": "user", "content": user_prompt}
            ],
            **LLMConfig.get_openai_params_multiple()
        )

        # Pobierz i parsuj odpowiedź
        content = response.choices[0].message.content.strip()
        content = self._clean_json_response(content)
        questions_data = json.loads(content)

        # Waliduj strukturę
        self._validate_multiple_questions(questions_data, count)

        logger.info(f"Generated {len(questions_data)} diverse AI questions successfully")
        return questions_data

    def _generate_ai_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        """Generuje pytanie używając OpenAI API"""
        user_prompt = QuizPrompts.build_single_question_prompt(
            topic, difficulty, subtopic, knowledge_level
        )

        # Wywołaj OpenAI API
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": QuizPrompts.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            **LLMConfig.get_openai_params_single()
        )

        # Pobierz i parsuj odpowiedź
        content = response.choices[0].message.content.strip()
        content = self._clean_json_response(content)
        question_data = json.loads(content)

        # Waliduj strukturę
        self._validate_single_question(question_data)

        logger.info("AI question generated successfully")
        return question_data

    def _clean_json_response(self, content):
        """Usuwa markdown code blocks z odpowiedzi"""
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _validate_single_question(self, question_data):
        """Waliduje strukturę pojedynczego pytania"""
        required_keys = ["question", "correct_answer", "wrong_answers", "explanation"]
        if not all(key in question_data for key in required_keys):
            raise ValueError(f"Missing required keys in response. Got: {question_data.keys()}")

        if len(question_data["wrong_answers"]) != 3:
            raise ValueError(f"Expected 3 wrong answers, got {len(question_data['wrong_answers'])}")

    def _validate_multiple_questions(self, questions_data, expected_count):
        """Waliduje strukturę wielu pytań"""
        if not isinstance(questions_data, list):
            raise ValueError(f"Expected list of questions, got: {type(questions_data)}")

        if len(questions_data) != expected_count:
            logger.warning(f"Requested {expected_count} questions but got {len(questions_data)}")

        for i, q_data in enumerate(questions_data):
            try:
                self._validate_single_question(q_data)
            except ValueError as e:
                raise ValueError(f"Question {i+1}: {e}")

    def _generate_fallback_question(self, topic, difficulty):
        """Generuje przykładowe pytanie gdy OpenAI nie jest dostępny"""
        questions_by_topic = {
            "Matematyka": [
                {
                    'question': 'Ile wynosi suma kątów w trójkącie?',
                    'correct_answer': '180 stopni',
                    'wrong_answers': ['90 stopni', '360 stopni', '270 stopni'],
                    'explanation': 'Suma kątów w dowolnym trójkącie zawsze wynosi 180 stopni.'
                },
                {
                    'question': 'Co to jest liczba pierwsza?',
                    'correct_answer': 'Liczba podzielna tylko przez 1 i siebie',
                    'wrong_answers': ['Liczba nieparzysta', 'Liczba większa od 10', 'Liczba dodatnia'],
                    'explanation': 'Liczba pierwsza to liczba naturalna większa od 1, która ma dokładnie dwa dzielniki: 1 i samą siebie.'
                },
            ],
            "Historia": [
                {
                    'question': 'W którym roku Polska odzyskała niepodległość?',
                    'correct_answer': '1918',
                    'wrong_answers': ['1914', '1920', '1945'],
                    'explanation': 'Polska odzyskała niepodległość 11 listopada 1918 roku po 123 latach zaborów.'
                },
                {
                    'question': 'Kto był pierwszym królem Polski?',
                    'correct_answer': 'Bolesław Chrobry',
                    'wrong_answers': ['Mieszko I', 'Kazimierz Wielki', 'Władysław Łokietek'],
                    'explanation': 'Bolesław Chrobry został koronowany na pierwszego króla Polski w 1025 roku.'
                },
            ],
            "Geografia": [
                {
                    'question': 'Jaka jest stolica Polski?',
                    'correct_answer': 'Warszawa',
                    'wrong_answers': ['Kraków', 'Gdańsk', 'Poznań'],
                    'explanation': 'Warszawa jest stolicą Polski od 1596 roku.'
                },
                {
                    'question': 'Który ocean jest największy?',
                    'correct_answer': 'Ocean Spokojny',
                    'wrong_answers': ['Ocean Atlantycki', 'Ocean Indyjski', 'Ocean Arktyczny'],
                    'explanation': 'Ocean Spokojny (Pacyfik) jest największym oceanem na Ziemi, zajmuje około 46% powierzchni oceanów.'
                },
            ],
        }

        default_questions = [
            {
                'question': 'Ile kontynentów jest na Ziemi?',
                'correct_answer': '7',
                'wrong_answers': ['5', '6', '8'],
                'explanation': 'Na Ziemi jest 7 kontynentów: Afryka, Antarktyda, Azja, Australia, Europa, Ameryka Północna i Ameryka Południowa.'
            },
            {
                'question': 'Ile wynosi 2 + 2?',
                'correct_answer': '4',
                'wrong_answers': ['3', '5', '22'],
                'explanation': 'Podstawowe działanie arytmetyczne: 2 + 2 = 4.'
            },
            {
                'question': 'Jakiego koloru jest niebo w pogodny dzień?',
                'correct_answer': 'Niebieskie',
                'wrong_answers': ['Zielone', 'Czerwone', 'Żółte'],
                'explanation': 'Niebo jest niebieskie z powodu rozpraszania światła (rozpraszanie Rayleigha).'
            },
        ]

        # Wybierz pytania dla danego tematu
        topic_questions = None
        for key in questions_by_topic:
            if key.lower() in topic.lower():
                topic_questions = questions_by_topic[key]
                break

        questions = topic_questions if topic_questions else default_questions
        return random.choice(questions)