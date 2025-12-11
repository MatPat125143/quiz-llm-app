import logging

logger = logging.getLogger(__name__)


class DifficultyAdapter:
    def __init__(self):
        self.streak_threshold = 2
        # NOWE: Asymetryczne kroki - szybsze wzrosty, wolniejsze spadki
        self.difficulty_step_up = 1.0    # Szybciej w górę
        self.difficulty_step_down = 0.75  # Wolniej w dół
        self.min_difficulty = 1.0
        self.max_difficulty = 10.0

        # NOWE: Równe przedziały 3.0 dla każdego poziomu
        # easy: 1.0-4.0 (przedział 3.0)
        # medium: 4.0-7.0 (przedział 3.0)
        # hard: 7.0-10.0 (przedział 3.0)
        self.easy_max = 4.0
        self.medium_max = 7.0  # Zmniejszone z 7.5

        # Punkty startowe w ŚRODKU każdego przedziału
        self.initial_difficulty_map = {
            'łatwy': 2.5,    # Środek 1.0-4.0
            'średni': 5.5,   # Środek 4.0-7.0
            'trudny': 8.5    # Środek 7.0-10.0
        }

        self.min_questions_count = 5
        self.max_questions_count = 20

    def get_initial_difficulty(self, difficulty_text):
        """
        Pobiera początkowy poziom trudności (float) dla podanego poziomu tekstowego.
        Wartość jest ustawiona w ŚRODKU przedziału.

        Args:
            difficulty_text: 'łatwy', 'średni' lub 'trudny'

        Returns:
            float: Początkowy poziom trudności (środek przedziału)
        """
        return self.initial_difficulty_map.get(difficulty_text, 5.5)

    def get_difficulty_level(self, difficulty_float):
        """
        Konwertuje numeryczny poziom trudności na tekstowy.

        Args:
            difficulty_float: Poziom trudności 1.0-10.0

        Returns:
            str: 'łatwy', 'średni' lub 'trudny'
        """
        if difficulty_float <= self.easy_max:
            return 'łatwy'
        elif difficulty_float <= self.medium_max:
            return 'średni'
        else:
            return 'trudny'

    def calculate_batch_size(self, total_questions, answered_count):
        """
        Oblicza rozmiar serii pytań do wygenerowania.
        Maksymalnie 10 pytań na serię, ale nie więcej niż zostało do końca gry.

        Args:
            total_questions: Łączna liczba pytań w grze (5-20)
            answered_count: Liczba pytań, na które już odpowiedzianoReturns:
            int: Liczba pytań do wygenerowania (max 10)
        """
        remaining = total_questions - answered_count
        return min(10, max(1, remaining))

    def should_pregenerate_next_level(self, current_difficulty, recent_answers, answered_count, total_questions):
        """
        Sprawdza czy należy preemptywnie wygenerować pytania na nowy poziom trudności.
        NOWE: Generuje JESZCZE WCZEŚNIEJ - już przy streak-1 odpowiedzi.

        Args:
            current_difficulty: Obecny poziom trudności (float)
            recent_answers: Lista ostatnich odpowiedzi (True/False)
            answered_count: Liczba odpowiedzianych pytań
            total_questions: Łączna liczba pytań w grze

        Returns:
            dict: {'should_pregenerate': bool, 'target_level': str or None}
        """
        # NOWE: Generuj już przy streak-1 odpowiedzi (np. po 1 odpowiedzi zamiast 2)
        # To daje więcej czasu na generowanie PRZED faktyczną zmianą poziomu
        min_answers_for_precheck = max(1, self.streak_threshold - 1)

        if len(recent_answers) < min_answers_for_precheck:
            return {'should_pregenerate': False, 'target_level': None}

        if answered_count >= total_questions:
            return {'should_pregenerate': False, 'target_level': None}

        current_level = self.get_difficulty_level(current_difficulty)

        # Sprawdź ostatnie N-1 odpowiedzi (wcześniejsza detekcja)
        check_count = min(len(recent_answers), self.streak_threshold - 1) if len(recent_answers) < self.streak_threshold else self.streak_threshold
        last_n = recent_answers[-check_count:]

        # Jeśli wszystkie poprawne → zbliża się wzrost poziomu
        if all(last_n):
            predicted_difficulty = current_difficulty + self.difficulty_step_up
            predicted_difficulty = min(self.max_difficulty, predicted_difficulty)
            predicted_level = self.get_difficulty_level(predicted_difficulty)

            if predicted_level != current_level:
                logger.info(f"Pre-generation (early): {current_level} -> {predicted_level} (streak={len(last_n)}/{self.streak_threshold} correct)")
                return {'should_pregenerate': True, 'target_level': predicted_level}

        # Jeśli wszystkie błędne → zbliża się spadek poziomu
        if not any(last_n):
            predicted_difficulty = current_difficulty - self.difficulty_step_down
            predicted_difficulty = max(self.min_difficulty, predicted_difficulty)
            predicted_level = self.get_difficulty_level(predicted_difficulty)

            if predicted_level != current_level:
                logger.info(f"Pre-generation (early): {current_level} -> {predicted_level} (streak={len(last_n)}/{self.streak_threshold} wrong)")
                return {'should_pregenerate': True, 'target_level': predicted_level}

        return {'should_pregenerate': False, 'target_level': None}

    def adjust_difficulty(self, current_difficulty, recent_answers):
        """
        Dostosowuje poziom trudności na podstawie ostatnich odpowiedzi.
        NOWE: Asymetryczne kroki - szybsze wzrosty (1.0), wolniejsze spadki (0.75)

        Args:
            current_difficulty: Obecny poziom trudności (float 1.0-10.0)
            recent_answers: Lista ostatnich odpowiedzi (True/False)

        Returns:
            float: Nowy poziom trudności
        """
        if len(recent_answers) < self.streak_threshold:
            return current_difficulty

        last_n_answers = recent_answers[-self.streak_threshold:]

        # Wszystkie poprawne → DUŻY SKOK W GÓRĘ
        if all(last_n_answers):
            new_difficulty = current_difficulty + self.difficulty_step_up
            return min(self.max_difficulty, new_difficulty)

        # Wszystkie błędne → MAŁY SKOK W DÓŁ (wolniejszy spadek)
        if not any(last_n_answers):
            new_difficulty = current_difficulty - self.difficulty_step_down
            return max(self.min_difficulty, new_difficulty)

        # Mixed (częściowo poprawne)
        correct_count = sum(last_n_answers)

        if correct_count > len(last_n_answers) / 2:
            # Więcej poprawnych niż błędnych → mały wzrost
            new_difficulty = current_difficulty + (self.difficulty_step_up / 2)
            return min(self.max_difficulty, new_difficulty)
        else:
            # Więcej błędnych → mały spadek (jeszcze wolniejszy)
            new_difficulty = current_difficulty - (self.difficulty_step_down / 2)
            return max(self.min_difficulty, new_difficulty)

    def adjust_difficulty_with_level_check(self, current_difficulty, recent_answers):
        """
        Dostosowuje poziom trudności i zwraca informację o zmianie POZIOMU (łatwy/średni/trudny).

        Args:
            current_difficulty: Obecny poziom trudności (float 1.0-10.0)
            recent_answers: Lista ostatnich odpowiedzi (True/False)

        Returns:
            dict: {
                'new_difficulty': float,
                'difficulty_changed': bool (czy zmienił się numerycznie),
                'level_changed': bool (czy zmienił się poziom tekstowy łatwy/średni/trudny),
                'previous_level': str,
                'new_level': str
            }
        """
        previous_level = self.get_difficulty_level(current_difficulty)
        new_difficulty = self.adjust_difficulty(current_difficulty, recent_answers)
        new_level = self.get_difficulty_level(new_difficulty)

        return {
            'new_difficulty': new_difficulty,
            'difficulty_changed': new_difficulty != current_difficulty,
            'level_changed': previous_level != new_level,
            'previous_level': previous_level,
            'new_level': new_level
        }