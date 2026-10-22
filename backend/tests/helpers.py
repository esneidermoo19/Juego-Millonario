from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app import create_app
from backend.models import Question
from backend.services.game_service import displayed_correct_letter, questions_for_game


class ApiTestCase(unittest.TestCase):
    """Crea una app con una base SQLite temporal y un banco de preguntas de prueba."""

    QUESTION_COUNT = 15

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = (Path(self.temp_dir.name) / "test.db").as_posix()
        self.config = {"TESTING": True, "DATABASE_URL": f"sqlite:///{database_path}"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.session_factory = self.app.extensions["database_session_factory"]
        self.seed_questions(self.QUESTION_COUNT)

    def tearDown(self):
        self.app.extensions["database_engine"].dispose()
        self.temp_dir.cleanup()

    def seed_questions(self, count: int) -> None:
        with self.session_factory() as session:
            for difficulty in range(1, count + 1):
                session.add(Question(
                    text=f"Pregunta {difficulty}",
                    option_a=f"Correcta {difficulty}",
                    option_b=f"Incorrecta B {difficulty}",
                    option_c=f"Incorrecta C {difficulty}",
                    option_d=f"Incorrecta D {difficulty}",
                    correct_option="A",
                    difficulty=difficulty,
                ))
            session.commit()

    def create_player(self, name: str = "Jugador") -> dict:
        response = self.client.post("/api/players", json={"name": name})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def create_game(self, player_name: str = "Jugador") -> dict:
        player = self.create_player(player_name)
        response = self.client.post("/api/games", json={"player_id": player["id"]})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def game_questions(self, game_id: int) -> list[Question]:
        with self.session_factory() as session:
            return questions_for_game(session, game_id)

    def correct_letter(self, question: Question, game_id: int) -> str:
        return displayed_correct_letter(question, game_id)

    def wrong_letter(self, question: Question, game_id: int) -> str:
        correct = self.correct_letter(question, game_id)
        return next(letter for letter in "ABCD" if letter != correct)

    def answer(self, game_id: int, question: Question, letter: str):
        return self.client.post(
            f"/api/games/{game_id}/answers",
            json={"question_id": question.id, "answer": letter},
        )

    def answer_correctly(self, game_id: int, count: int) -> dict:
        result = {}
        for question in self.game_questions(game_id)[:count]:
            response = self.answer(game_id, question, self.correct_letter(question, game_id))
            self.assertEqual(response.status_code, 200)
            result = response.get_json()
        return result
