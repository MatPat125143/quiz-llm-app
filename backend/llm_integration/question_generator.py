import os
import json
import random
import logging

logger = logging.getLogger('llm_integration')


class QuestionGenerator:

    def __init__(self):
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY", "")

        if not self.api_key or self.api_key == "sk-your-openai-api-key-here":
            logger.warning("OPENAI_API_KEY not set - using fallback questions")
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.warning("openai package not installed - using fallback questions")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")

    def _get_knowledge_level_description(self, knowledge_level):
        descriptions = {
            'elementary': 'szkoła podstawowa (klasy 1-8)',
            'high_school': 'liceum (szkoła średnia)',
            'university': 'studia wyższe',
            'expert': 'poziom ekspercki (zaawansowany)'
        }
        return descriptions.get(knowledge_level, 'liceum (szkoła średnia)')

    def generate_multiple_questions(self, topic, difficulty, count, subtopic=None, knowledge_level='high_school'):
        if isinstance(difficulty, (int, float)):
            from llm_integration.difficulty_adapter import DifficultyAdapter
            adapter = DifficultyAdapter()
            difficulty_text = adapter.get_difficulty_level(difficulty)
        else:
            difficulty_text = difficulty

        if self.client is None:
            logger.info(f"Generating {count} fallback questions for topic: {topic}, difficulty: {difficulty_text}")
            return [self._generate_fallback_question(topic, difficulty_text) for _ in range(count)]

        try:
            logger.info(f"Generating {count} DIVERSE AI questions for topic: {topic}, subtopic: {subtopic}, knowledge: {knowledge_level}, difficulty: {difficulty_text}")
            return self._generate_multiple_ai_questions(topic, difficulty_text, count, subtopic, knowledge_level)
        except Exception as e:
            logger.error(f"Error generating multiple AI questions: {e}")
            logger.info("Falling back to predefined questions")
            return [self._generate_fallback_question(topic, difficulty_text) for _ in range(count)]

    def _generate_multiple_ai_questions(self, topic, difficulty, count, subtopic=None, knowledge_level='high_school'):
        difficulty_descriptions = {
            'łatwy': 'podstawowy, odpowiedni dla początkujących',
            'średni': 'umiarkowany, wymaga pewnej wiedzy',
            'trudny': 'zaawansowany, dla ekspertów'
        }
        difficulty_desc = difficulty_descriptions.get(difficulty, 'umiarkowany')

        knowledge_desc = self._get_knowledge_level_description(knowledge_level)
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        system_prompt = """Jesteś ekspertem od tworzenia pytań edukacyjnych.
Tworzysz pytania quizowe w języku polskim.
ZAWSZE odpowiadasz w formacie JSON bez dodatkowego tekstu.
WAŻNE: Pytania muszą być RÓŻNORODNE i dotyczyć RÓŻNYCH aspektów tematu!"""

        user_prompt = f"""Wygeneruj {count} RÓŻNORODNYCH pytań quizowych:
- Temat: {topic}{subtopic_info}
- Poziom edukacyjny ucznia: {knowledge_desc}
- Poziom trudności pytania: {difficulty} ({difficulty_desc})
- WAŻNE: Każde pytanie musi dotyczyć INNEGO aspektu tematu!
- WAŻNE: Unikaj powtarzania tego samego typu pytań!
- WAŻNE: Zmień kontekst, liczby, przykłady w każdym pytaniu!
- WAŻNE: Dostosuj język i złożoność do poziomu: {knowledge_desc}

Zwróć odpowiedź w DOKŁADNIE tym formacie JSON (tablica {count} pytań):
[
  {{
    "question": "treść pytania 1 po polsku (dostosowana do poziomu {knowledge_desc})",
    "correct_answer": "poprawna odpowiedź 1",
    "wrong_answers": ["błędna 1.1", "błędna 1.2", "błędna 1.3"],
    "explanation": "krótkie wyjaśnienie 1 po polsku (dostosowane do poziomu {knowledge_desc})"
  }},
  {{
    "question": "treść pytania 2 po polsku (INNY aspekt tematu!)",
    "correct_answer": "poprawna odpowiedź 2",
    "wrong_answers": ["błędna 2.1", "błędna 2.2", "błędna 2.3"],
    "explanation": "krótkie wyjaśnienie 2 po polsku"
  }}
  ... (pozostałe pytania)
]"""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()
        content = self._clean_json_response(content)
        questions_data = json.loads(content)

        if not isinstance(questions_data, list):
            raise ValueError(f"Expected list of questions, got: {type(questions_data)}")

        if len(questions_data) != count:
            logger.warning(f"Requested {count} questions but got {len(questions_data)}")

        for i, q_data in enumerate(questions_data):
            required_keys = ["question", "correct_answer", "wrong_answers", "explanation"]
            if not all(key in q_data for key in required_keys):
                raise ValueError(f"Question {i+1} missing required keys. Got: {q_data.keys()}")

            if len(q_data["wrong_answers"]) != 3:
                raise ValueError(f"Question {i+1} has {len(q_data['wrong_answers'])} wrong answers, expected 3")

        logger.info(f"Generated {len(questions_data)} diverse AI questions successfully")
        return questions_data

    def generate_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        if isinstance(difficulty, (int, float)):
            from llm_integration.difficulty_adapter import DifficultyAdapter
            adapter = DifficultyAdapter()
            difficulty_text = adapter.get_difficulty_level(difficulty)
        else:
            difficulty_text = difficulty

        if self.client is None:
            logger.info(f"Generating fallback question for topic: {topic}, difficulty: {difficulty_text}")
            return self._generate_fallback_question(topic, difficulty_text)

        try:
            logger.info(f"Generating AI question for topic: {topic}, subtopic: {subtopic}, knowledge: {knowledge_level}, difficulty: {difficulty_text}")
            return self._generate_ai_question(topic, difficulty_text, subtopic, knowledge_level)
        except Exception as e:
            logger.error(f"Error generating AI question: {e}")
            logger.info("Falling back to predefined questions")
            return self._generate_fallback_question(topic, difficulty_text)

    def _generate_ai_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        difficulty_descriptions = {
            'łatwy': 'podstawowy, odpowiedni dla początkujących',
            'średni': 'umiarkowany, wymaga pewnej wiedzy',
            'trudny': 'zaawansowany, dla ekspertów'
        }
        difficulty_desc = difficulty_descriptions.get(difficulty, 'umiarkowany')

        knowledge_desc = self._get_knowledge_level_description(knowledge_level)
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        system_prompt = """Jesteś ekspertem od tworzenia pytań edukacyjnych.
Tworzysz pytania quizowe w języku polskim.
ZAWSZE odpowiadasz w formacie JSON bez dodatkowego tekstu."""

        user_prompt = f"""Wygeneruj pytanie quizowe:
- Temat: {topic}{subtopic_info}
- Poziom edukacyjny ucznia: {knowledge_desc}
- Poziom trudności pytania: {difficulty} ({difficulty_desc})
- WAŻNE: Dostosuj język i złożoność do poziomu: {knowledge_desc}

Zwróć odpowiedź w DOKŁADNIE tym formacie JSON:
{{
    "question": "treść pytania po polsku (dostosowana do poziomu {knowledge_desc})",
    "correct_answer": "poprawna odpowiedź",
    "wrong_answers": ["błędna odpowiedź 1", "błędna odpowiedź 2", "błędna odpowiedź 3"],
    "explanation": "krótkie wyjaśnienie poprawnej odpowiedzi po polsku (dostosowane do poziomu {knowledge_desc})"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()
        content = self._clean_json_response(content)
        question_data = json.loads(content)

        required_keys = ["question", "correct_answer", "wrong_answers", "explanation"]
        if not all(key in question_data for key in required_keys):
            raise ValueError(f"Missing required keys in response. Got: {question_data.keys()}")

        if len(question_data["wrong_answers"]) != 3:
            raise ValueError(f"Expected 3 wrong answers, got {len(question_data['wrong_answers'])}")

        logger.info("AI question generated successfully")
        return question_data

    def _clean_json_response(self, content):
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _generate_fallback_question(self, topic, difficulty):
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

        topic_questions = None
        for key in questions_by_topic:
            if key.lower() in topic.lower():
                topic_questions = questions_by_topic[key]
                break

        questions = topic_questions if topic_questions else default_questions
        return random.choice(questions)