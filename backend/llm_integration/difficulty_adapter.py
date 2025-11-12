class DifficultyAdapter:
    def __init__(self):
        self.streak_threshold = 2  # Zmniejszono z 3 na 2 dla szybszej adaptacji
        self.difficulty_step = 0.75  # Zwiększono z 0.5 na 0.75 dla większych skoków
        self.min_difficulty = 1.0
        self.max_difficulty = 10.0

        # ✅ PROGI POZIOMÓW TRUDNOŚCI - TYLKO 3 POZIOMY!
        self.easy_max = 3.5  # łatwy: 1.0 - 3.5
        self.medium_max = 7.0  # średni: 3.51 - 7.0
        # trudny: 7.01 - 10.0

    def get_difficulty_level(self, difficulty_float):
        """
        Konwertuje numeryczny poziom trudności na tekstowy.
        TYLKO 3 POZIOMY: łatwy, średni, trudny

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

    def adjust_difficulty(self, current_difficulty, recent_answers):
        """
        Dostosowuje poziom trudności na podstawie ostatnich odpowiedzi.

        Args:
            current_difficulty: Obecny poziom trudności (float 1.0-10.0)
            recent_answers: Lista ostatnich odpowiedzi (True/False)

        Returns:
            float: Nowy poziom trudności
        """
        if len(recent_answers) < self.streak_threshold:
            return current_difficulty

        last_n_answers = recent_answers[-self.streak_threshold:]

        if all(last_n_answers):
            new_difficulty = current_difficulty + self.difficulty_step
            return min(self.max_difficulty, new_difficulty)

        if not any(last_n_answers):
            new_difficulty = current_difficulty - self.difficulty_step
            return max(self.min_difficulty, new_difficulty)

        correct_count = sum(last_n_answers)

        if correct_count > len(last_n_answers) / 2:
            new_difficulty = current_difficulty + (self.difficulty_step / 2)
            return min(self.max_difficulty, new_difficulty)
        else:
            new_difficulty = current_difficulty - (self.difficulty_step / 2)
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