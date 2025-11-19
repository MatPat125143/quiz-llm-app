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
            # POPRAWKA: Bez 'proxies' parametru
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI client initialized successfully")
        except ImportError:
            print("⚠️  openai package not installed - using fallback questions")
        except Exception as e:
            print(f"⚠️  Failed to initialize OpenAI: {e}")

    def _convert_numeric_to_text_difficulty(self, difficulty_float):
        """
        Konwertuje numeryczny poziom trudności na tekstowy.

        Args:
            difficulty_float: Poziom trudności 1.0-10.0

        Returns:
            str: 'łatwy', 'średni' lub 'trudny'
        """
        if difficulty_float <= 3.5:
            return 'łatwy'
        elif difficulty_float <= 7.0:
            return 'średni'
        else:
            return 'trudny'

    def _get_knowledge_level_description(self, knowledge_level):
        """
        Zwraca opis poziomu wiedzy dla promptu AI.

        Args:
            knowledge_level: 'elementary', 'high_school', 'university', 'expert'

        Returns:
            str: Opis poziomu po polsku
        """
        descriptions = {
            'elementary': 'szkoła podstawowa (klasy 1-8)',
            'high_school': 'liceum (szkoła średnia)',
            'university': 'studia wyższe',
            'expert': 'poziom ekspercki (zaawansowany)'
        }
        return descriptions.get(knowledge_level, 'liceum (szkoła średnia)')

    def generate_multiple_questions(self, topic, difficulty, count, subtopic=None, knowledge_level='high_school'):
        """
        Generuje wiele RÓŻNORODNYCH pytań na raz.
        Używane dla stałych poziomów trudności.

        Args:
            topic (str): Temat pytań (np. "Matematyka", "Historia")
            difficulty (float): Poziom trudności 1-10 (lub str: 'łatwy', 'średni', 'trudny')
            count (int): Ile pytań wygenerować
            subtopic (str): Podtemat (np. "Algebra", "Geometria") - opcjonalnie
            knowledge_level (str): Poziom wiedzy ('elementary', 'high_school', 'university', 'expert')

        Returns:
            list: Lista słowników z pytaniami
        """
        # Konwertuj numeryczny poziom na tekstowy jeśli potrzeba
        if isinstance(difficulty, (int, float)):
            difficulty_text = self._convert_numeric_to_text_difficulty(difficulty)
        else:
            difficulty_text = difficulty

        # Jeśli brak klienta OpenAI, użyj fake questions
        if self.client is None:
            print(f"📝 Generating {count} fallback questions for topic: {topic}, difficulty: {difficulty_text}")
            return [self._generate_fallback_question(topic, difficulty_text) for _ in range(count)]

        # Generuj pytania używając OpenAI
        try:
            print(f"🤖 Generating {count} DIVERSE AI questions for topic: {topic}, subtopic: {subtopic}, knowledge: {knowledge_level}, difficulty: {difficulty_text}")
            return self._generate_multiple_ai_questions(topic, difficulty_text, count, subtopic, knowledge_level)
        except Exception as e:
            print(f"❌ Error generating multiple AI questions: {e}")
            print(f"📝 Falling back to predefined questions")
            return [self._generate_fallback_question(topic, difficulty_text) for _ in range(count)]

    def _generate_multiple_ai_questions(self, topic, difficulty, count, subtopic=None, knowledge_level='high_school'):
        """Generuje wiele różnorodnych pytań używając OpenAI API"""

        # Mapuj poziom trudności na opis dla AI
        difficulty_descriptions = {
            'łatwy': 'podstawowy, odpowiedni dla początkujących',
            'średni': 'umiarkowany, wymaga pewnej wiedzy',
            'trudny': 'zaawansowany, dla ekspertów'
        }
        difficulty_desc = difficulty_descriptions.get(difficulty, 'umiarkowany')

        # Opis poziomu wiedzy
        knowledge_desc = self._get_knowledge_level_description(knowledge_level)

        # Informacja o podtemacie
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        # Przygotuj prompt dla AI-WAŻNE: podkreśl różnorodność!
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

✅ ZASADY DLA ODPOWIEDZI:
- Odpowiedzi muszą być KRÓTKIE i KONKRETNE (tylko wynik/wartość/nazwa)
- NIE powtarzaj treści pytania w odpowiedzi
- Przykład DOBRZE: Pytanie "Ile wynosi 2+2?" → Odpowiedź "4"
- Przykład ŹLE: Pytanie "Ile wynosi 2+2?" → Odpowiedź "2+2=4" lub "Suma wynosi 4"
- Odpowiedź to TYLKO wynik, bez dodatkowego tekstu!

Zwróć odpowiedź w DOKŁADNIE tym formacie JSON (tablica {count} pytań):
[
  {{
    "question": "treść pytania 1 po polsku (dostosowana do poziomu {knowledge_desc})",
    "correct_answer": "poprawna odpowiedź 1 (KRÓTKA, tylko wynik!)",
    "wrong_answers": ["błędna 1.1 (krótka)", "błędna 1.2 (krótka)", "błędna 1.3 (krótka)"],
    "explanation": "krótkie wyjaśnienie 1 po polsku (dostosowane do poziomu {knowledge_desc})"
  }},
  {{
    "question": "treść pytania 2 po polsku (INNY aspekt tematu!)",
    "correct_answer": "poprawna odpowiedź 2 (KRÓTKA, tylko wynik!)",
    "wrong_answers": ["błędna 2.1 (krótka)", "błędna 2.2 (krótka)", "błędna 2.3 (krótka)"],
    "explanation": "krótkie wyjaśnienie 2 po polsku"
  }}
  ... (pozostałe pytania)
]"""

        # Wywołaj OpenAI API z większym max_tokens dla wielu pytań
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,  # Wyższa temperatura = więcej różnorodności
            max_tokens=2000  # Więcej tokenów dla wielu pytań
        )

        # Pobierz odpowiedź
        content = response.choices[0].message.content.strip()

        # Oczyść odpowiedź z markdown code blocks
        content = self._clean_json_response(content)

        # Parsuj JSON
        questions_data = json.loads(content)

        # Waliduj strukturę
        if not isinstance(questions_data, list):
            raise ValueError(f"Expected list of questions, got: {type(questions_data)}")

        if len(questions_data) != count:
            print(f"⚠️ Requested {count} questions but got {len(questions_data)}")

        # Waliduj każde pytanie
        for i, q_data in enumerate(questions_data):
            required_keys = ["question", "correct_answer", "wrong_answers", "explanation"]
            if not all(key in q_data for key in required_keys):
                raise ValueError(f"Question {i+1} missing required keys. Got: {q_data.keys()}")

            if len(q_data["wrong_answers"]) != 3:
                raise ValueError(f"Question {i+1} has {len(q_data['wrong_answers'])} wrong answers, expected 3")

        print(f"✅ Generated {len(questions_data)} diverse AI questions successfully")
        return questions_data

    def generate_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        """
        Generuje pytanie quizowe

        Args:
            topic (str): Temat pytania (np. "Matematyka", "Historia")
            difficulty (float lub str): Poziom trudności 1-10 lub 'łatwy'/'średni'/'trudny'
            subtopic (str): Podtemat (np. "Algebra", "Geometria") - opcjonalnie
            knowledge_level (str): Poziom wiedzy ('elementary', 'high_school', 'university', 'expert')

        Returns:
            dict: Słownik z pytaniem, odpowiedziami i wyjaśnieniem
        """
        # Konwertuj numeryczny poziom na tekstowy jeśli potrzeba
        if isinstance(difficulty, (int, float)):
            difficulty_text = self._convert_numeric_to_text_difficulty(difficulty)
        else:
            difficulty_text = difficulty

        # Jeśli brak klienta OpenAI, użyj fake questions
        if self.client is None:
            print(f"📝 Generating fallback question for topic: {topic}, difficulty: {difficulty_text}")
            return self._generate_fallback_question(topic, difficulty_text)

        # Generuj pytanie używając OpenAI
        try:
            print(f"🤖 Generating AI question for topic: {topic}, subtopic: {subtopic}, knowledge: {knowledge_level}, difficulty: {difficulty_text}")
            return self._generate_ai_question(topic, difficulty_text, subtopic, knowledge_level)
        except Exception as e:
            print(f"❌ Error generating AI question: {e}")
            print(f"📝 Falling back to predefined questions")
            return self._generate_fallback_question(topic, difficulty_text)

    def _generate_ai_question(self, topic, difficulty, subtopic=None, knowledge_level='high_school'):
        """Generuje pytanie używając OpenAI API"""

        # Mapuj poziom trudności na opis dla AI
        difficulty_descriptions = {
            'łatwy': 'podstawowy, odpowiedni dla początkujących',
            'średni': 'umiarkowany, wymaga pewnej wiedzy',
            'trudny': 'zaawansowany, dla ekspertów'
        }
        difficulty_desc = difficulty_descriptions.get(difficulty, 'umiarkowany')

        # Opis poziomu wiedzy
        knowledge_desc = self._get_knowledge_level_description(knowledge_level)

        # Informacja o podtemacie
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        # Przygotuj prompt dla AI
        system_prompt = """Jesteś ekspertem od tworzenia pytań edukacyjnych.
Tworzysz pytania quizowe w języku polskim.
ZAWSZE odpowiadasz w formacie JSON bez dodatkowego tekstu."""

        user_prompt = f"""Wygeneruj pytanie quizowe:
- Temat: {topic}{subtopic_info}
- Poziom edukacyjny ucznia: {knowledge_desc}
- Poziom trudności pytania: {difficulty} ({difficulty_desc})
- WAŻNE: Dostosuj język i złożoność do poziomu: {knowledge_desc}

✅ ZASADY DLA ODPOWIEDZI:
- Odpowiedzi muszą być KRÓTKIE i KONKRETNE (tylko wynik/wartość/nazwa)
- NIE powtarzaj treści pytania w odpowiedzi
- Przykład DOBRZE: Pytanie "Ile wynosi 2+2?" → Odpowiedź "4"
- Przykład ŹLE: Pytanie "Ile wynosi 2+2?" → Odpowiedź "2+2=4" lub "Suma wynosi 4"
- Odpowiedź to TYLKO wynik, bez dodatkowego tekstu!

Zwróć odpowiedź w DOKŁADNIE tym formacie JSON:
{{
    "question": "treść pytania po polsku (dostosowana do poziomu {knowledge_desc})",
    "correct_answer": "poprawna odpowiedź (KRÓTKA, tylko wynik!)",
    "wrong_answers": ["błędna 1 (krótka)", "błędna 2 (krótka)", "błędna 3 (krótka)"],
    "explanation": "krótkie wyjaśnienie poprawnej odpowiedzi po polsku (dostosowane do poziomu {knowledge_desc})"
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