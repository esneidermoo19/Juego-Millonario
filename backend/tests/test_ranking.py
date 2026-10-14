from __future__ import annotations

import unittest

from backend.tests.helpers import ApiTestCase


class RankingTests(ApiTestCase):
    def finish_with(self, name: str, correct_answers: int) -> dict:
        """Partida que acierta `correct_answers` y falla la siguiente."""
        game = self.create_game(name)
        self.answer_correctly(game["id"], correct_answers)
        if correct_answers < 15:
            question = self.game_questions(game["id"])[correct_answers]
            self.answer(game["id"], question, self.wrong_letter(question, game["id"]))
        return game

    def test_empty_ranking(self):
        self.assertEqual(self.client.get("/api/ranking").get_json(), [])

    def test_ranking_is_sorted_by_prize(self):
        self.finish_with("Bronce", 2)
        self.finish_with("Oro", 15)
        self.finish_with("Plata", 6)
        rows = self.client.get("/api/ranking").get_json()
        self.assertEqual([row["player_name"] for row in rows], ["Oro", "Plata", "Bronce"])
        self.assertEqual([row["score"] for row in rows], [1_000_000, 2000, 200])

    def test_ranking_row_fields(self):
        game = self.finish_with("Ana", 3)
        row = self.client.get("/api/ranking").get_json()[0]
        self.assertEqual(row["game_id"], game["id"])
        self.assertEqual(row["player_id"], game["player_id"])
        self.assertEqual(row["player_name"], "Ana")
        self.assertEqual(row["score"], 300)
        self.assertIsNotNone(row["finished_at"])

    def test_tie_goes_to_whoever_finished_first(self):
        self.finish_with("Primero", 4)
        self.finish_with("Segundo", 4)
        names = [row["player_name"] for row in self.client.get("/api/ranking").get_json()]
        self.assertEqual(names, ["Primero", "Segundo"])

    def test_games_in_progress_are_excluded(self):
        self.create_game("En curso")
        self.finish_with("Terminó", 1)
        names = [row["player_name"] for row in self.client.get("/api/ranking").get_json()]
        self.assertEqual(names, ["Terminó"])

    def test_abandoned_games_are_excluded(self):
        # Comportamiento actual: quien se retira no aparece en el ranking.
        game = self.create_game("Se retiró")
        self.answer_correctly(game["id"], 5)
        self.client.post(f"/api/games/{game['id']}/quit")
        self.assertEqual(self.client.get("/api/ranking").get_json(), [])

    def test_limit_parameter(self):
        for index in range(4):
            self.finish_with(f"Jugador {index}", index)
        self.assertEqual(len(self.client.get("/api/ranking?limit=2").get_json()), 2)
        self.assertEqual(len(self.client.get("/api/ranking").get_json()), 4)

    def test_invalid_limit_is_rejected(self):
        for limit in ["0", "101", "-5", "diez"]:
            with self.subTest(limit=limit):
                self.assertEqual(self.client.get(f"/api/ranking?limit={limit}").status_code, 400)


if __name__ == "__main__":
    unittest.main()
