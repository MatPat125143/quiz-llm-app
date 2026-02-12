from django.test import SimpleTestCase

from llm_integration.difficulty_adapter import DifficultyAdapter


class DifficultyAdapterTests(SimpleTestCase):
    def setUp(self):
        self.adapter = DifficultyAdapter()

    def test_initial_difficulty_and_level_mapping(self):
        self.assertEqual(self.adapter.get_initial_difficulty('łatwy'), 2.5)
        self.assertEqual(self.adapter.get_initial_difficulty('średni'), 5.5)
        self.assertEqual(self.adapter.get_initial_difficulty('trudny'), 8.5)
        self.assertEqual(self.adapter.get_initial_difficulty('unknown'), 5.5)

        self.assertEqual(self.adapter.get_difficulty_level(1.0), 'łatwy')
        self.assertEqual(self.adapter.get_difficulty_level(4.0), 'łatwy')
        self.assertEqual(self.adapter.get_difficulty_level(4.1), 'średni')
        self.assertEqual(self.adapter.get_difficulty_level(7.0), 'średni')
        self.assertEqual(self.adapter.get_difficulty_level(7.1), 'trudny')

    def test_adjust_difficulty_up_down_and_mixed(self):
        self.assertEqual(self.adapter.adjust_difficulty(5.0, [True, True]), 6.0)
        self.assertEqual(self.adapter.adjust_difficulty(5.0, [False, False]), 4.25)
        self.assertEqual(self.adapter.adjust_difficulty(5.0, [True, False]), 4.625)
        self.assertEqual(self.adapter.adjust_difficulty(5.0, [False, True]), 4.625)

    def test_adjust_with_level_check_flags_level_change(self):
        result = self.adapter.adjust_difficulty_with_level_check(4.0, [True, True])
        self.assertTrue(result['difficulty_changed'])
        self.assertTrue(result['level_changed'])
        self.assertEqual(result['previous_level'], 'łatwy')
        self.assertEqual(result['new_level'], 'średni')

    def test_should_pregenerate_next_level_detects_transition(self):
        should = self.adapter.should_pregenerate_next_level(
            current_difficulty=4.0,
            recent_answers=[True, True],
            answered_count=2,
            total_questions=10
        )
        self.assertTrue(should['should_pregenerate'])
        self.assertEqual(should['target_level'], 'średni')

        should_not = self.adapter.should_pregenerate_next_level(
            current_difficulty=5.5,
            recent_answers=[True],
            answered_count=1,
            total_questions=10
        )
        self.assertFalse(should_not['should_pregenerate'])
