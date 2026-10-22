from __future__ import annotations

import unittest

from backend.tests.helpers import ApiTestCase


class GameCrudTests(ApiTestCase):
    def test_create_game_starts_in_progress(self):
        game = self.create_game()
        self.assertEqual(game["status"], "in_progress")
        self.assertEqual(game["score"], 0)
        self.assertEqual(game["current_question_number"], 0)
        self.assertIsNone(game["finished_at"])

    def test_create_game_validation(self):
        for payload in [{}, {"player_id": 0}, {"player_id": "1"}, {"player_id": True}, {"player_id": 1, "x": 1}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/games", json=payload).status_code, 400)

    def test_create_game_for_missing_player_conflicts(self):
        self.assertEqual(self.client.post("/api/games", json={"player_id": 999}).status_code, 409)

    def test_list_get_and_filter_games(self):
        first = self.create_game("Ana")
        second = self.create_game("Luis")
        self.assertEqual(len(self.client.get("/api/games").get_json()), 2)
        filtered = self.client.get(f"/api/games?player_id={second['player_id']}").get_json()
        self.assertEqual([game["id"] for game in filtered], [second["id"]])
        self.assertEqual(self.client.get(f"/api/games/{first['id']}").get_json()["id"], first["id"])
        self.assertEqual(self.client.get("/api/games/999").status_code, 404)
        self.assertEqual(self.client.get("/api/games?player_id=abc").status_code, 400)

    def test_update_and_delete_game(self):
        game = self.create_game()
        url = f"/api/games/{game['id']}"
        self.assertEqual(self.client.patch(url, json={"status": "abandoned"}).get_json()["status"], "abandoned")
        self.assertEqual(self.client.patch(url, json={"status": "ganado"}).status_code, 400)
        self.assertEqual(self.client.patch(url, json={"score": -1}).status_code, 400)
        self.assertEqual(self.client.put(url, json={"score": 1}).status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)


class GamePlayTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.game_id = self.create_game()["id"]
        self.questions = self.game_questions(self.game_id)

    def test_correct_answer_advances_and_pays(self):
        response = self.answer(self.game_id, self.questions[0], self.correct_letter(self.questions[0], self.game_id))
        self.assertEqual(response.get_json(), {"correct": True, "prize": 100, "game_finished": False})
        game = self.client.get(f"/api/games/{self.game_id}").get_json()
        self.assertEqual(game["current_question_number"], 1)
        self.assertEqual(game["score"], 100)

    def test_winning_all_fifteen_pays_one_million(self):
        result = self.answer_correctly(self.game_id, 15)
        self.assertEqual(result, {"correct": True, "prize": 1_000_000, "game_finished": True})
        game = self.client.get(f"/api/games/{self.game_id}").get_json()
        self.assertEqual(game["status"], "completed")
        self.assertIsNotNone(game["finished_at"])

    def test_wrong_answer_ends_game_and_reveals_correct_answer(self):
        self.answer_correctly(self.game_id, 7)
        question = self.questions[7]
        response = self.answer(self.game_id, question, self.wrong_letter(question, self.game_id)).get_json()
        self.assertFalse(response["correct"])
        self.assertTrue(response["game_finished"])
        self.assertEqual(response["prize"], 4000)
        self.assertEqual(response["correct_answer"], self.correct_letter(question, self.game_id))

    def test_wrong_first_answer_pays_nothing(self):
        question = self.questions[0]
        response = self.answer(self.game_id, question, self.wrong_letter(question, self.game_id))
        self.assertEqual(response.get_json()["prize"], 0)

    def test_answer_must_be_for_current_question(self):
        question = self.questions[1]
        response = self.answer(self.game_id, question, self.correct_letter(question, self.game_id))
        self.assertEqual(response.status_code, 400)

    def test_answer_validation(self):
        url = f"/api/games/{self.game_id}/answers"
        for payload in [{}, {"question_id": self.questions[0].id}, {"question_id": self.questions[0].id, "answer": "E"},
                        {"question_id": "1", "answer": "A"}, {"question_id": True, "answer": "A"}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(url, json=payload).status_code, 400)

    def test_cannot_answer_finished_game(self):
        self.client.post(f"/api/games/{self.game_id}/quit")
        question = self.questions[0]
        response = self.answer(self.game_id, question, self.correct_letter(question, self.game_id))
        self.assertEqual(response.status_code, 409)

    def test_answer_on_missing_game_returns_404(self):
        question = self.questions[0]
        self.assertEqual(self.answer(999, question, "A").status_code, 404)

    def test_timeout_keeps_prize_and_finishes(self):
        self.answer_correctly(self.game_id, 3)
        response = self.client.post(f"/api/games/{self.game_id}/timeout", json={"question_id": self.questions[3].id})
        self.assertEqual(response.get_json(), {"correct": False, "prize": 300, "game_finished": True})

    def test_timeout_validation(self):
        url = f"/api/games/{self.game_id}/timeout"
        self.assertEqual(self.client.post(url, json={}).status_code, 400)
        self.assertEqual(self.client.post(url, json={"question_id": self.questions[2].id}).status_code, 400)

    def test_quit_keeps_current_prize(self):
        self.answer_correctly(self.game_id, 10)
        response = self.client.post(f"/api/games/{self.game_id}/quit")
        self.assertEqual(response.get_json(), {"success": True, "final_prize": 32000})
        self.assertEqual(self.client.get(f"/api/games/{self.game_id}").get_json()["status"], "abandoned")
        self.assertEqual(self.client.post(f"/api/games/{self.game_id}/quit").status_code, 409)

    def test_finish_validation(self):
        url = f"/api/games/{self.game_id}/finish"
        self.assertEqual(self.client.post(url, json={}).status_code, 400)
        self.assertEqual(self.client.post(url, json={"won": "yes"}).status_code, 400)

    def test_finish_without_winning_keeps_score(self):
        self.answer_correctly(self.game_id, 2)
        response = self.client.post(f"/api/games/{self.game_id}/finish", json={"won": False})
        self.assertEqual(response.get_json()["final_prize"], 200)


if __name__ == "__main__":
    unittest.main()
