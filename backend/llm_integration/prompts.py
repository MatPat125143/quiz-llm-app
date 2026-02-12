class QuizPrompts:
    SYSTEM_PROMPT = """Tworzysz pytania quizowe po polsku. ZAWSZE zwracasz czysty JSON (bez komentarzy/tekstu).

CELE
- Pytanie adekwatne do poziomu wiedzy i trudności.
- Zachowaj wyraźną różnicę: łatwy/średni/trudny.
- Unikaj błędów merytorycznych i niejednoznaczności.

DOPASOWANIE (WEWNĘTRZNIE)
- Ustal poziom ucznia dla knowledge_level.
- Łatwy: proste pojęcie, małe liczby, 1 krok, bez pułapek.
- Średni: zrozumienie + 1–2 kroki, lekka pułapka.
- Trudny: 2–4 kroki, detale/wyjątki, precyzja.
- Nie przekraczaj poziomu wiedzy (np. SP bez całek).

ODPOWIEDZI
- Zawsze 4: 1 poprawna + 3 błędne, wiarygodne i tego samego typu.
- Odpowiedzi podobne (liczby/daty/nazwy), ale tylko jedna poprawna.
- Zakaz: „wszystkie powyższe”, „żadna z powyższych”, „nie wiem”.

UNIKAJ 50/50
- Nie twórz pytań z realnie 2–3 sensownymi opcjami.
- Jeśli temat jest binarny, przeredaguj tak, aby były 4 realistyczne warianty.
- Nie używaj konstrukcji typu „czy …” ani porównań dwóch elementów (np. „większa/mniejsza”, „prawda/fałsz”).

WALIDACJA (WEWNĘTRZNIE)
- Sprawdź poprawność obliczeń/faktów.
- Upewnij się, że błędne odpowiedzi są faktycznie błędne.
- Unikaj pytań wieloznacznych lub sprzecznych.

WYJAŚNIENIE
- Max 2 zdania, konkretne i poprawne merytorycznie.

FORMAT
- Zwróć dokładnie taki JSON, jak w poleceniu użytkownika."""

    SYSTEM_PROMPT_DIVERSE = """Tworzysz pytania quizowe po polsku. ZAWSZE zwracasz czysty JSON (bez komentarzy/tekstu).

CELE
- Każde pytanie bada INNY aspekt tematu/podtematu (zero parafraz i zmian samych liczb).
- Trudność i poziom wiedzy muszą być spójne.
- Odpowiedzi podobne, ale tylko jedna poprawna.

DOPASOWANIE (WEWNĘTRZNIE)
- Łatwy: 1 proste pojęcie, 1 krok.
- Średni: 1–2 kroki, zrozumienie.
- Trudny: 2–4 kroki, detale/wyjątki.
- Nie przekraczaj poziomu wiedzy.

ODPOWIEDZI
- Zawsze 4: 1 poprawna + 3 błędne, wiarygodne i tego samego typu.
- Zakaz: „wszystkie powyższe”, „żadna z powyższych”, „nie wiem”.

UNIKAJ 50/50
- Nie twórz pytań z realnie 2–3 sensownymi opcjami.
- Jeśli temat jest binarny, przeredaguj na 4 realistyczne warianty.
- Nie używaj konstrukcji typu „czy …” ani porównań dwóch elementów (np. „większa/mniejsza”, „prawda/fałsz”).

WYJAŚNIENIE
- Max 2 zdania, konkretne i poprawne.

FORMAT
- Zwróć dokładnie taki JSON, jak w poleceniu użytkownika."""

    DIFFICULTY_DESCRIPTIONS = {
        'łatwy': 'PODSTAWOWY - proste pytania, oczywiste odpowiedzi, fundamentalne pojęcia',
        'średni': 'UMIARKOWANY - wymaga rozumienia tematu, odpowiedzi wymagają zastanowienia',
        'trudny': 'ZAAWANSOWANY - głębokie zrozumienie, szczegóły, niuanse, przypadki brzegowe'
    }

    KNOWLEDGE_LEVEL_DESCRIPTIONS = {
        'elementary': 'szkoła podstawowa (klasy 1-8)',
        'high_school': 'liceum (szkoła średnia)',
        'university': 'studia wyższe',
        'expert': 'poziom ekspercki (zaawansowany)'
    }

    KNOWLEDGE_DIFFICULTY_MAPPING = {
        'elementary': {
            'łatwy': 'klasy 1-3 szkoły podstawowej (podstawowe pojęcia, proste obliczenia)',
            'średni': 'klasy 4-6 szkoły podstawowej (średniozaawansowane pojęcia)',
            'trudny': 'klasy 7-8 szkoły podstawowej (zaawansowane dla poziomu podstawowego)'
        },
        'high_school': {
            'łatwy': 'klasy 1-2 liceum (podstawy tematu)',
            'średni': 'klasy 2-3 liceum (pełne zrozumienie tematu)',
            'trudny': 'klasa 3 liceum + matura rozszerzona (zaawansowane zagadnienia)'
        },
        'university': {
            'łatwy': 'pierwszy rok studiów (wprowadzenie)',
            'średni': 'drugi-trzeci rok studiów (pełna wiedza)',
            'trudny': 'praca magisterska, zaawansowane kursy'
        },
        'expert': {
            'łatwy': 'profesjonalista (podstawy specjalizacji)',
            'średni': 'ekspert w dziedzinie (głęboka wiedza)',
            'trudny': 'światowy specjalista (cutting-edge knowledge)'
        }
    }

    @staticmethod
    def get_knowledge_description(knowledge_level):
        return QuizPrompts.KNOWLEDGE_LEVEL_DESCRIPTIONS.get(
            knowledge_level,
            'liceum (szkoła średnia)'
        )

    @staticmethod
    def get_difficulty_description(difficulty):
        return QuizPrompts.DIFFICULTY_DESCRIPTIONS.get(difficulty, 'umiarkowany')

    @staticmethod
    def get_detailed_level_description(knowledge_level, difficulty):
        if knowledge_level in QuizPrompts.KNOWLEDGE_DIFFICULTY_MAPPING:
            return QuizPrompts.KNOWLEDGE_DIFFICULTY_MAPPING[knowledge_level].get(
                difficulty,
                QuizPrompts.KNOWLEDGE_LEVEL_DESCRIPTIONS.get(knowledge_level, 'liceum')
            )
        return QuizPrompts.KNOWLEDGE_LEVEL_DESCRIPTIONS.get(knowledge_level, 'liceum')

    @staticmethod
    def build_single_question_prompt(topic, difficulty, subtopic=None, knowledge_level='high_school'):
        difficulty_desc = QuizPrompts.get_difficulty_description(difficulty)
        detailed_level = QuizPrompts.get_detailed_level_description(knowledge_level, difficulty)
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        return f"""Wygeneruj JEDNO pytanie quizowe:
- Temat główny: {topic}{subtopic_info}
- Docelowy poziom ucznia/wiedzy: {detailed_level}
- Poziom trudności: {difficulty} ({difficulty_desc})

WYMAGANIA DOTYCZĄCE DOPASOWANIA:
- Pytanie musi być NATURALNE dla poziomu "{detailed_level}" (ani zbyt łatwe, ani zbyt trudne).
- Osoba o poziomie NIŻSZYM powinna mieć realny problem z tym pytaniem.
- Osoba o poziomie WYŻSZYM powinna uznać je za stosunkowo proste.

WYMAGANIA MERYTORYCZNE:
- 1 pytanie ŚCIŚLE związane z tematem (i podtematem, jeśli podano).
- Pytanie musi mieć jednoznaczną poprawną odpowiedź.
- Unikaj pytań wieloznacznych i sprzecznych.

ODPOWIEDZI:
- 4 odpowiedzi: 1 POPRAWNA + 3 BŁĘDNE (łudząco podobne).
- Wszystkie odpowiedzi muszą dotyczyć tego samego pojęcia i mieć ten sam typ (np. wszystkie liczby).
- Żadna z błędnych odpowiedzi nie może być poprawna.

WYJAŚNIENIE:
- Maksymalnie 2 zdania,
- krótko wyjaśnij, dlaczego poprawna odpowiedź jest poprawna.

Format JSON:
{{
  "question": "treść pytania",
  "correct_answer": "poprawna odpowiedź",
  "wrong_answers": ["błędna 1", "błędna 2", "błędna 3"],
  "explanation": "krótkie wyjaśnienie"
}}"""

    @staticmethod
    def build_multiple_questions_prompt(
            topic,
            difficulty,
            count,
            subtopic=None,
            knowledge_level='high_school',
            existing_questions=None
    ):
        difficulty_desc = QuizPrompts.get_difficulty_description(difficulty)
        detailed_level = QuizPrompts.get_detailed_level_description(knowledge_level, difficulty)
        subtopic_info = f"\n- Podtemat: {subtopic}" if subtopic else ""

        context_info = ""
        if existing_questions and len(existing_questions) > 0:
            context_info = "\n\n=== NIE POWTARZAJ TYCH PYTAŃ ===\n"
            for i, q in enumerate(existing_questions[:15], 1):
                context_info += f"{i}. {q}\n"
            context_info += "\n=== Generuj NOWE, CAŁKOWICIE RÓŻNE pytania (zero parafraz, zero podobnych przykładów, zero tych samych liczb) ===\n"

        return f"""Wygeneruj {count} RÓŻNYCH pytań quizowych:
- Temat główny: {topic}{subtopic_info}
- Docelowy poziom ucznia/wiedzy: {detailed_level}
- Poziom trudności: {difficulty} ({difficulty_desc}){context_info}

DOPASOWANIE:
- Każde pytanie musi być adekwatne do poziomu "{detailed_level}".
- Trudność każdego pytania powinna odpowiadać poziomowi "{difficulty}".
- W całym zestawie ma być wyczuwalny ten sam poziom trudności (bez losowego mieszania bardzo łatwych i bardzo trudnych pytań).

RÓŻNORODNOŚĆ:
- Każde pytanie musi dotyczyć INNEGO aspektu tematu (inne pojęcie, inny przypadek, inny szczegół).
- Nie powtarzaj schematów typu: „zmień tylko liczby” – zmieniaj również aspekt merytoryczny.

WYMAGANIA DLA KAŻDEGO PYTANIA:
- Jednoznaczne pytanie mające dokładnie jedną poprawną odpowiedź.
- 4 odpowiedzi: 1 POPRAWNA + 3 BŁĘDNE (łudząco podobne, ten sam typ odpowiedzi).
- Żadna z błędnych odpowiedzi nie może być poprawna.
- Wyjaśnienie: maksymalnie 2 zdania, poprawne merytorycznie.
- SPRAWDŹ logikę i poprawność merytoryczną pytania PRZED zwróceniem odpowiedzi.

Format JSON – tablica {count} pytań:
[
  {{
    "question": "pytanie 1",
    "correct_answer": "poprawna 1",
    "wrong_answers": ["błędna 1a", "błędna 1b", "błędna 1c"],
    "explanation": "wyjaśnienie 1"
  }},
  {{
    "question": "pytanie 2 (inny aspekt tematu)",
    "correct_answer": "poprawna 2",
    "wrong_answers": ["błędna 2a", "błędna 2b", "błędna 2c"],
    "explanation": "wyjaśnienie 2"
  }}
]"""
