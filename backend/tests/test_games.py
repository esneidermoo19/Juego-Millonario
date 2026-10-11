from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app import create_app
from backend.models import Game, Player, Question
from backend.services.game_service import displayed_correct_letter, questions_for_game


class EarnedPrizeFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = (Path(self.temp_dir.name) / "game-test.db").as_posix()
        self.config = {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{database_path}",
        }
        self.app = create_app(self.config)
        self.apps = [self.app]
        self.client = self.app.test_client()

        factory = self.app.extensions["database_session_factory"]
        with factory() as session:
            player = Player(name="Prize test")
            session.add(player)
            session.flush()
            for difficulty in range(1, 4):
                session.add(Question(
                    text=f"Question {difficulty}",
                    option_a="Correct",
                    option_b="Wrong B",
                    option_c="Wrong C",
                    option_d="Wrong D",
                    correct_option="A",
                    difficulty=difficulty,
                ))
            game = Game(player_id=player.id)
            session.add(game)
            session.commit()
            self.game_id = game.id

    def tearDown(self):
        for app in self.apps:
            app.extensions["database_engine"].dispose()
        self.temp_dir.cleanup()

    def get_game_questions(self):
        factory = self.app.extensions["database_session_factory"]
        with factory() as session:
            return questions_for_game(session, self.game_id)

    def answer_correctly(self, question):
        letter = displayed_correct_letter(question, self.game_id)
        response = self.client.post(
            f"/api/games/{self.game_id}/answers",
            json={"question_id": question.id, "answer": letter},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["correct"])

    def test_wrong_answer_preserves_earned_prize_in_result_and_ranking(self):
        questions = self.get_game_questions()
        self.answer_correctly(questions[0])
        self.answer_correctly(questions[1])
        correct_letter = displayed_correct_letter(questions[2], self.game_id)
        wrong_letter = next(letter for letter in "ABCD" if letter != correct_letter)

        response = self.client.post(
            f"/api/games/{self.game_id}/answers",
            json={"question_id": questions[2].id, "answer": wrong_letter},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["prize"], 200)
        ranking = self.client.get("/api/ranking").get_json()
        self.assertEqual(ranking[0]["score"], 200)

    def test_timeout_preserves_earned_prize_in_result_and_ranking(self):
        questions = self.get_game_questions()
        self.answer_correctly(questions[0])
        self.answer_correctly(questions[1])

        response = self.client.post(
            f"/api/games/{self.game_id}/timeout",
            json={"question_id": questions[2].id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["prize"], 200)
        ranking = self.client.get("/api/ranking").get_json()
        self.assertEqual(ranking[0]["score"], 200)

    def test_startup_repairs_legacy_completed_game_score(self):
        factory = self.app.extensions["database_session_factory"]
        with factory() as session:
            game = session.get(Game, self.game_id)
            game.current_question_number = 2
            game.score = 0
            game.status = "completed"
            session.commit()

        repaired_app = create_app(self.config)
        self.apps.append(repaired_app)
        ranking = repaired_app.test_client().get("/api/ranking").get_json()
        self.assertEqual(ranking[0]["score"], 200)


if __name__ == "__main__":
    unittest.main()
