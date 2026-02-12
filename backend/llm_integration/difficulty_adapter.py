import logging

logger = logging.getLogger(__name__)


class DifficultyAdapter:
    def __init__(self):
        self.streak_threshold = 2

        self.difficulty_step_up = 1.0
        self.difficulty_step_down = 0.75
        self.min_difficulty = 1.0
        self.max_difficulty = 10.0

        self.easy_max = 4.0
        self.medium_max = 7.0

        self.initial_difficulty_map = {
            'łatwy': 2.5,
            'średni': 5.5,
            'trudny': 8.5
        }

    def get_initial_difficulty(self, difficulty_text):
        return self.initial_difficulty_map.get(difficulty_text, 5.5)

    def get_difficulty_level(self, difficulty_float):
        if difficulty_float <= self.easy_max:
            return 'łatwy'
        elif difficulty_float <= self.medium_max:
            return 'średni'
        else:
            return 'trudny'

    def should_pregenerate_next_level(
            self, current_difficulty, recent_answers, answered_count, total_questions
    ):

        min_answers_for_precheck = max(1, self.streak_threshold - 1)

        if len(recent_answers) < min_answers_for_precheck:
            return {'should_pregenerate': False, 'target_level': None}

        if answered_count >= total_questions:
            return {'should_pregenerate': False, 'target_level': None}

        current_level = self.get_difficulty_level(current_difficulty)

        check_count = (
            min(len(recent_answers), self.streak_threshold - 1)
            if len(recent_answers) < self.streak_threshold
            else self.streak_threshold
        )
        last_n = recent_answers[-check_count:]

        if all(last_n):
            predicted_difficulty = current_difficulty + self.difficulty_step_up
            predicted_difficulty = min(self.max_difficulty, predicted_difficulty)
            predicted_level = self.get_difficulty_level(predicted_difficulty)

            if predicted_level != current_level:
                logger.info(
                    "Pre-generation (early): %s -> %s (streak=%s/%s correct)",
                    current_level,
                    predicted_level,
                    len(last_n),
                    self.streak_threshold,
                )
                return {'should_pregenerate': True, 'target_level': predicted_level}

        if not any(last_n):
            predicted_difficulty = current_difficulty - self.difficulty_step_down
            predicted_difficulty = max(self.min_difficulty, predicted_difficulty)
            predicted_level = self.get_difficulty_level(predicted_difficulty)

            if predicted_level != current_level:
                logger.info(
                    "Pre-generation (early): %s -> %s (streak=%s/%s wrong)",
                    current_level,
                    predicted_level,
                    len(last_n),
                    self.streak_threshold,
                )
                return {'should_pregenerate': True, 'target_level': predicted_level}

        return {'should_pregenerate': False, 'target_level': None}

    def adjust_difficulty(self, current_difficulty, recent_answers):
        if len(recent_answers) < self.streak_threshold:
            return current_difficulty

        last_n_answers = recent_answers[-self.streak_threshold:]

        if all(last_n_answers):
            new_difficulty = current_difficulty + self.difficulty_step_up
            return min(self.max_difficulty, new_difficulty)

        if not any(last_n_answers):
            new_difficulty = current_difficulty - self.difficulty_step_down
            return max(self.min_difficulty, new_difficulty)

        correct_count = sum(last_n_answers)

        if correct_count > len(last_n_answers) / 2:

            new_difficulty = current_difficulty + (self.difficulty_step_up / 2)
            return min(self.max_difficulty, new_difficulty)
        else:

            new_difficulty = current_difficulty - (self.difficulty_step_down / 2)
            return max(self.min_difficulty, new_difficulty)

    def adjust_difficulty_with_level_check(self, current_difficulty, recent_answers):
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
