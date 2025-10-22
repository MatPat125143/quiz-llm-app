class DifficultyAdapter:
    def __init__(self):
        self.streak_threshold = 2  # Zmniejszono z 3 na 2 dla szybszej adaptacji
        self.difficulty_step = 0.75  # Zwiększono z 0.5 na 0.75 dla większych skoków
        self.min_difficulty = 1.0
        self.max_difficulty = 10.0

    def adjust_difficulty(self, current_difficulty, recent_answers):
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

    def get_difficulty_description(self, difficulty):
        if difficulty <= 3:
            return "Easy"
        elif difficulty <= 6:
            return "Medium"
        elif difficulty <= 8:
            return "Hard"
        else:
            return "Expert"