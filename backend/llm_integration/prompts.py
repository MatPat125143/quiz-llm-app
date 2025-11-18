"""
Prompty systemowe i użytkownika dla generowania pytań quizowych
"""


class QuizPrompts:
    """Prompty dla generowania pytań quizowych"""

    SYSTEM_PROMPT = """Jesteś ekspertem od tworzenia pytań edukacyjnych.
Tworzysz pytania quizowe w języku polskim.
ZAWSZE odpowiadasz w formacie JSON bez dodatkowego tekstu."""

    SYSTEM_PROMPT_DIVERSE = """Jesteś ekspertem od tworzenia pytań edukacyjnych.
Tworzysz pytania quizowe w języku polskim.
ZAWSZE odpowiadasz w formacie JSON bez dodatkowego tekstu.
WAŻNE: Pytania muszą być RÓŻNORODNE i dotyczyć RÓŻNYCH aspektów tematu!"""

    DIFFICULTY_DESCRIPTIONS = {
        'łatwy': 'podstawowy, odpowiedni dla początkujących',
        'średni': 'umiarkowany, wymaga pewnej wiedzy',
        'trudny': 'zaawansowany, dla ekspertów'
    }

    KNOWLEDGE_LEVEL_DESCRIPTIONS = {
        'elementary': 'szkoła podstawowa (klasy 1-8)',
        'high_school': 'liceum (szkoła średnia)',
        'university': 'studia wyższe',
        'expert': 'poziom ekspercki (zaawansowany)'
    }

    @staticmethod
    def get_knowledge_description(knowledge_level):
        """Pobierz opis poziomu wiedzy"""
        return QuizPrompts.KNOWLEDGE_LEVEL_DESCRIPTIONS.get(
            knowledge_level,
            'liceum (szkoła średnia)'
        )

    @staticmethod
    def get_difficulty_description(difficulty):
        """Pobierz opis trudności"""
        return QuizPrompts.DIFFICULTY_DESCRIPTIONS.get(difficulty, 'umiarkowany')

    @staticmethod
    def build_single_question_prompt(topic, difficulty, subtopic=None, knowledge_level='high_school'):
        """Buduje prompt dla pojedynczego pytania"""
        difficulty_desc = QuizPrompts.get_difficulty_description(difficulty)
        knowledge_desc = QuizPrompts.get_knowledge_description(knowledge_level)
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        return f"""Wygeneruj pytanie quizowe:
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

    @staticmethod
    def build_multiple_questions_prompt(topic, difficulty, count, subtopic=None, knowledge_level='high_school'):
        """Buduje prompt dla wielu pytań"""
        difficulty_desc = QuizPrompts.get_difficulty_description(difficulty)
        knowledge_desc = QuizPrompts.get_knowledge_description(knowledge_level)
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        return f"""Wygeneruj {count} RÓŻNORODNYCH pytań quizowych:
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