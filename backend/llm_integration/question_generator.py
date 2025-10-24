"""
Generator pytań quizowych używający OpenAI API
"""
import os
import json
import random


class QuestionGenerator:
    """Klasa do generowania pytań quizowych"""

    def __init__(self):
        """Inicjalizacja generatora pytań"""
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY", "")

        # Sprawdź czy klucz API jest ustawiony
        if not self.api_key or self.api_key == "sk-your-openai-api-key-here":
            print("⚠️  OPENAI_API_KEY not set - using fallback questions")
            return

        # Inicjalizuj klienta OpenAI
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI client initialized successfully with gpt-3.5-turbo")
        except ImportError:
            print("⚠️  openai package not installed - using fallback questions")
        except Exception as e:
            print(f"⚠️  Failed to initialize OpenAI: {e}")

    def generate_question(self, topic, difficulty):
        """
        Generuje pytanie quizowe

        Args:
            topic (str): Temat pytania (np. "Matematyka", "Historia")
            difficulty (float): Poziom trudności 1-10

        Returns:
            dict: Słownik z pytaniem, odpowiedziami i wyjaśnieniem
        """
        # Jeśli brak klienta OpenAI, użyj fake questions
        if self.client is None:
            print(f"📝 Generating fallback question for topic: {topic}, difficulty: {difficulty}")
            return self._generate_fallback_question(topic, difficulty)

        # Generuj pytanie używając OpenAI
        try:
            print(f"🤖 Generating AI question for topic: {topic}, difficulty: {difficulty}")
            return self._generate_ai_question(topic, difficulty)
        except Exception as e:
            print(f"❌ Error generating AI question: {e}")
            print(f"📝 Falling back to predefined questions")
            return self._generate_fallback_question(topic, difficulty)

    def _generate_ai_question(self, topic, difficulty):
        """Generuje pytanie używając OpenAI API"""

        # Przygotuj prompt dla AI
        system_prompt = """Jesteś ekspertem od tworzenia pytań edukacyjnych.
Tworzysz pytania quizowe w języku polskim.
ZAWSZE odpowiadasz w formacie JSON bez dodatkowego tekstu."""

        user_prompt = f"""Wygeneruj pytanie quizowe:
- Temat: {topic}
- Poziom trudności: {difficulty}/10

Zwróć odpowiedź w DOKŁADNIE tym formacie JSON:
{{
    "question": "treść pytania po polsku",
    "correct_answer": "poprawna odpowiedź",
    "wrong_answers": ["błędna odpowiedź 1", "błędna odpowiedź 2", "błędna odpowiedź 3"],
    "explanation": "krótkie wyjaśnienie poprawnej odpowiedzi po polsku"
}}"""

        # Wywołaj OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )

        # Pobierz odpowiedź
        content = response.choices[0].message.content.strip()

        # Oczyść odpowiedź z markdown code blocks
        content = self._clean_json_response(content)

        # Parsuj JSON
        question_data = json.loads(content)

        # Waliduj strukturę
        required_keys = ["question", "correct_answer", "wrong_answers", "explanation"]
        if not all(key in question_data for key in required_keys):
            raise ValueError(f"Missing required keys in response. Got: {question_data.keys()}")

        if len(question_data["wrong_answers"]) != 3:
            raise ValueError(f"Expected 3 wrong answers, got {len(question_data['wrong_answers'])}")

        print(f"✅ AI question generated successfully")
        return question_data

    def _clean_json_response(self, content):
        """Usuwa markdown code blocks z odpowiedzi"""
        # Usuń ```json na początku
        if content.startswith("```json"):
            content = content[7:]
        # Usuń ``` na początku
        if content.startswith("```"):
            content = content[3:]
        # Usuń ``` na końcu
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    def _generate_fallback_question(self, topic, difficulty):
        """Generuje przykładowe pytanie gdy OpenAI nie jest dostępny"""

        # Różne pytania zależnie od tematu
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

        # Domyślne pytania jeśli temat nie pasuje
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

        # Użyj pytań tematycznych lub domyślnych
        questions = topic_questions if topic_questions else default_questions

        return random.choice(questions)
