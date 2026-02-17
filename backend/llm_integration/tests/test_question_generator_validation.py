from django.test import SimpleTestCase
from unittest.mock import patch

from llm_integration.question_generator import QuestionGenerator


class QuestionGeneratorValidationTests(SimpleTestCase):
    def setUp(self):
        self.generator = QuestionGenerator()

    def _valid_question(self):
        return {
            "question": "Ktore miasto jest stolica Francji?",
            "correct_answer": "Paryz",
            "wrong_answers": ["Berlin", "Madryt", "Rzym"],
            "explanation": "Stolica Francji to Paryz.",
        }

    def test_validate_single_question_accepts_valid_payload(self):
        payload = self._valid_question()
        self.generator._validate_single_question(payload)

    def test_validate_single_question_rejects_duplicate_answers(self):
        payload = self._valid_question()
        payload["wrong_answers"][0] = "Paryz"

        with self.assertRaisesMessage(ValueError, "4 unique options"):
            self.generator._validate_single_question(payload)

    def test_validate_single_question_rejects_binary_question(self):
        payload = self._valid_question()
        payload["question"] = "Prawda czy falsz: 2 + 2 = 4?"

        with self.assertRaisesMessage(ValueError, "binary/50-50"):
            self.generator._validate_single_question(payload)

    def test_validate_multiple_questions_filters_invalid_items(self):
        valid = self._valid_question()
        invalid = {
            "question": "Prawda czy falsz: Ziemia jest plaska?",
            "correct_answer": "Nie",
            "wrong_answers": ["Tak", "Nie", "Brak"],
            "explanation": "To pytanie testowe.",
        }

        result = self.generator._validate_multiple_questions([valid, invalid], expected_count=2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["correct_answer"], "Paryz")

    def test_validate_multiple_questions_raises_when_all_invalid(self):
        invalid = {
            "question": "Wybierz jedna z 3 opcji.",
            "correct_answer": "A",
            "wrong_answers": ["A", "B", "C"],
            "explanation": "To pytanie testowe.",
        }

        with self.assertRaisesMessage(ValueError, "No valid questions"):
            self.generator._validate_multiple_questions([invalid], expected_count=1)

    def test_validate_single_question_requires_explanation_to_include_answer(self):
        payload = self._valid_question()
        payload["explanation"] = "To odpowiedz wynikajaca z faktu geograficznego."

        with self.assertRaisesMessage(ValueError, "Explanation must explicitly include the correct answer"):
            self.generator._validate_single_question(payload)

    def test_validate_single_question_rejects_greater_less_binary_style(self):
        payload = self._valid_question()
        payload["question"] = "Ktora liczba jest wieksza: 8 czy 5?"
        payload["correct_answer"] = "8"
        payload["wrong_answers"] = ["5", "6", "7"]
        payload["explanation"] = "Poprawna odpowiedz to 8, bo 8 > 5."

        with self.assertRaisesMessage(ValueError, "binary/50-50"):
            self.generator._validate_single_question(payload)

    def test_validate_single_question_rejects_ambiguous_decimal_without_rounding(self):
        payload = {
            "question": "Ile wynosi pierwiastek z 2?",
            "correct_answer": "1.41421356",
            "wrong_answers": ["1.2", "1.5", "2.0"],
            "explanation": "Poprawna odpowiedz to 1.41421356.",
        }

        with self.assertRaisesMessage(ValueError, "missing rounding instruction"):
            self.generator._validate_single_question(payload)

    def test_validate_single_question_rejects_wrong_basic_arithmetic_result(self):
        payload = {
            "question": "Oblicz 7 + 8.",
            "correct_answer": "20",
            "wrong_answers": ["14", "15", "16"],
            "explanation": "Poprawna odpowiedz to 20.",
        }

        with self.assertRaisesMessage(ValueError, "does not match the arithmetic result"):
            self.generator._validate_single_question(payload)

    def test_validate_single_question_accepts_linear_equation_result(self):
        payload = {
            "question": "Rozwiaz rownanie 3a = 15.",
            "correct_answer": "5",
            "wrong_answers": ["3", "6", "8"],
            "explanation": "Poprawna odpowiedz to 5, bo 15/3 = 5.",
        }

        self.generator._validate_single_question(payload)

    def test_validate_single_question_accepts_multi_step_expression_without_false_reject(self):
        payload = {
            "question": "Oblicz 2 + 2 + 2.",
            "correct_answer": "6",
            "wrong_answers": ["4", "5", "8"],
            "explanation": "Poprawna odpowiedz to 6.",
        }

        self.generator._validate_single_question(payload)

    def test_validate_single_question_accepts_non_math_question_with_numbers(self):
        payload = {
            "question": "W ktorym roku odbyla sie premiera filmu Incepcja?",
            "correct_answer": "2010",
            "wrong_answers": ["2008", "2009", "2012"],
            "explanation": "Poprawna odpowiedz to 2010.",
        }

        self.generator._validate_single_question(payload)

    def test_validate_single_question_rejects_forbidden_meta_option(self):
        payload = {
            "question": "Ktore z ponizszych panstw lezy w Europie?",
            "correct_answer": "Niemcy",
            "wrong_answers": ["Brazylia", "Zadna z powyzszych", "Kanada"],
            "explanation": "Poprawna odpowiedz to Niemcy.",
        }

        with self.assertRaisesMessage(ValueError, "forbidden option patterns"):
            self.generator._validate_single_question(payload)

    def test_generate_multiple_questions_falls_back_when_batch_returns_no_valid(self):
        self.generator.client = object()
        first = self._valid_question()
        second = {
            "question": "Ktore miasto jest stolica Wloch?",
            "correct_answer": "Rzym",
            "wrong_answers": ["Mediolan", "Neapol", "Turyn"],
            "explanation": "Poprawna odpowiedz to Rzym.",
        }

        with patch.object(
            self.generator,
            "_generate_multiple_ai_questions",
            side_effect=ValueError("No valid questions returned by model"),
        ), patch.object(
            self.generator,
            "_generate_ai_question",
            side_effect=[first, second],
        ) as single_mock:
            result = self.generator.generate_multiple_questions(
                topic="Geografia",
                difficulty="latwy",
                count=2,
            )

        self.assertEqual(len(result), 2)
        self.assertEqual(single_mock.call_count, 2)

    def test_generate_multiple_questions_raises_when_fallback_generates_nothing(self):
        self.generator.client = object()

        with patch.object(
            self.generator,
            "_generate_multiple_ai_questions",
            side_effect=ValueError("No valid questions returned by model"),
        ), patch.object(
            self.generator,
            "_generate_ai_question",
            side_effect=ValueError("bad payload"),
        ):
            with self.assertRaisesMessage(ValueError, "No valid questions returned by model"):
                self.generator.generate_multiple_questions(
                    topic="Geografia",
                    difficulty="latwy",
                    count=1,
                )

    def test_generate_multiple_questions_fallback_skips_existing_question_text(self):
        self.generator.client = object()
        duplicate = self._valid_question()
        unique = {
            "question": "Ktory ocean jest najwiekszy?",
            "correct_answer": "Ocean Spokojny",
            "wrong_answers": ["Ocean Atlantycki", "Ocean Indyjski", "Ocean Arktyczny"],
            "explanation": "Poprawna odpowiedz to Ocean Spokojny.",
        }

        with patch.object(
            self.generator,
            "_generate_multiple_ai_questions",
            side_effect=ValueError("No valid questions returned by model"),
        ), patch.object(
            self.generator,
            "_generate_ai_question",
            side_effect=[duplicate, unique],
        ) as single_mock:
            result = self.generator.generate_multiple_questions(
                topic="Geografia",
                difficulty="latwy",
                count=1,
                existing_questions=["Ktore miasto jest stolica Francji?"],
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["question"], unique["question"])
        self.assertEqual(single_mock.call_count, 2)
