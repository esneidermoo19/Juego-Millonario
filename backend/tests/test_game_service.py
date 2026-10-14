from __future__ import annotations

import unittest

from backend.models import Question
from backend.services.game_service import (
    displayed_correct_letter,
    options_for_game,
    questions_for_game,
)
from backend.services.prizes import PRIZES, prize_for_correct_answers
from backend.tests.helpers import ApiTestCase


def make_question(question_id: int, correct: str = "A") -> Question:
    return Question(
        id=question_id,
        text=f"Pregunta {question_id}",
        option_a="Opción A",
        option_b="Opción B",
        option_c="Opción C",
        option_d="Opción D",
        correct_option=correct,
        difficulty=question_id,
    )


class PrizeTests(unittest.TestCase):
    def test_ladder_has_fifteen_increasing_prizes(self):
        self.assertEqual(len(PRIZES), 15)
        self.assertEqual(list(PRIZES), sorted(PRIZES))
        self.assertEqual(PRIZES[0], 100)
        self.assertEqual(PRIZES[-1], 1_000_000)

    def test_no_correct_answers_means_no_prize(self):
        self.assertEqual(prize_for_correct_answers(0), 0)
        self.assertEqual(prize_for_correct_answers(-3), 0)

    def test_prize_matches_ladder_step(self):
        self.assertEqual(prize_for_correct_answers(1), 100)
        self.assertEqual(prize_for_correct_answers(5), 1000)
        self.assertEqual(prize_for_correct_answers(10), 32000)
        self.assertEqual(prize_for_correct_answers(15), 1_000_000)

    def test_prize_never_exceeds_top_of_ladder(self):
        self.assertEqual(prize_for_correct_answers(40), 1_000_000)


class OptionShuffleTests(unittest.TestCase):
    def test_options_keep_all_original_answers(self):
        question = make_question(7)
        options = options_for_game(question, game_id=3)
        self.assertEqual(sorted(letter for letter, _ in options), ["A", "B", "C", "D"])
        self.assertEqual(
            sorted(text for _, text in options),
            ["Opción A", "Opción B", "Opción C", "Opción D"],
        )

    def test_shuffle_is_repeatable_for_the_same_game(self):
        question = make_question(7)
        self.assertEqual(options_for_game(question, 3), options_for_game(question, 3))

    def test_displayed_correct_letter_points_to_correct_text(self):
        for correct in "ABCD":
            question = make_question(11, correct)
            for game_id in range(1, 20):
                letter = displayed_correct_letter(question, game_id)
                displayed = dict(zip("ABCD", (text for _, text in options_for_game(question, game_id))))
                self.assertEqual(displayed[letter], f"Opción {correct}")

    def test_invalid_correct_option_raises(self):
        question = make_question(2, correct="Z")
        with self.assertRaises(ValueError):
            displayed_correct_letter(question, 1)


class QuestionSelectionTests(ApiTestCase):
    QUESTION_COUNT = 30

    def test_selects_fifteen_unique_questions(self):
        questions = self.game_questions(1)
        self.assertEqual(len(questions), 15)
        self.assertEqual(len({question.id for question in questions}), 15)

    def test_selection_is_repeatable_per_game(self):
        first = [question.id for question in self.game_questions(4)]
        second = [question.id for question in self.game_questions(4)]
        self.assertEqual(first, second)

    def test_different_games_can_get_different_questions(self):
        selections = {tuple(q.id for q in self.game_questions(game_id)) for game_id in range(1, 6)}
        self.assertGreater(len(selections), 1)

    def test_difficulty_bands_go_from_easy_to_hard(self):
        difficulties = [question.difficulty for question in self.game_questions(2)]
        easy, medium, hard = difficulties[:5], difficulties[5:10], difficulties[10:]
        self.assertLess(max(easy), min(medium))
        self.assertLess(max(medium), min(hard))


class SmallQuestionBankTests(ApiTestCase):
    QUESTION_COUNT = 1

    def test_bank_with_one_question_returns_it(self):
        self.assertEqual(len(self.game_questions(1)), 1)


if __name__ == "__main__":
    unittest.main()
