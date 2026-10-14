from __future__ import annotations

import unittest

from backend.tests.helpers import ApiTestCase


class UseLifelineTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game()
        self.game_id = self.game["id"]
        self.current = self.game_questions(self.game_id)[0]
        self.correct = self.correct_letter(self.current, self.game_id)

    def use(self, kind: str, language: str | None = None):
        url = f"/api/games/{self.game_id}/lifelines/{kind}"
        if language:
            url += f"?language={language}"
        return self.client.post(url)

    def test_fifty_fifty_removes_two_wrong_options(self):
        response = self.use("5050")
        self.assertEqual(response.status_code, 200)
        removed = response.get_json()["removed_options"]
        self.assertEqual(len(removed), 2)
        self.assertEqual(len(set(removed)), 2)
        self.assertNotIn(self.correct, removed)

    def test_audience_percentages_add_up_and_favor_correct_answer(self):
        percentages = self.use("audience").get_json()["percentages"]
        self.assertEqual(set(percentages), {"A", "B", "C", "D"})
        self.assertEqual(sum(percentages.values()), 100)
        self.assertEqual(max(percentages, key=percentages.get), self.correct)

    def test_friend_suggests_correct_answer_in_spanish(self):
        message = self.use("friend").get_json()["message"]
        self.assertTrue(message.startswith("Creo que la respuesta correcta es"))
        self.assertIn(f"es {self.correct}:", message)

    def test_friend_suggests_correct_answer_in_english(self):
        message = self.use("friend", "en").get_json()["message"]
        self.assertTrue(message.startswith("I think the correct answer is"))
        self.assertIn(f"is {self.correct}:", message)

    def test_each_lifeline_can_be_used_only_once(self):
        for kind in ("5050", "audience", "friend"):
            with self.subTest(kind=kind):
                self.assertEqual(self.use(kind).status_code, 200)
                self.assertEqual(self.use(kind).status_code, 409)

    def test_unknown_lifeline_returns_404(self):
        self.assertEqual(self.use("phone").status_code, 404)

    def test_lifeline_not_allowed_on_finished_game(self):
        self.client.post(f"/api/games/{self.game_id}/quit")
        self.assertEqual(self.use("5050").status_code, 409)

    def test_lifeline_on_missing_game_returns_404(self):
        self.assertEqual(self.client.post("/api/games/999/lifelines/5050").status_code, 404)

    def test_used_lifeline_is_recorded(self):
        self.use("audience")
        lifelines = self.client.get("/api/lifelines").get_json()
        self.assertEqual([(item["game_id"], item["kind"]) for item in lifelines], [(self.game_id, "audience")])
        self.assertIsNotNone(lifelines[0]["used_at"])


class LifelineCrudTests(ApiTestCase):
    def test_create_get_update_and_delete(self):
        game = self.create_game()
        created = self.client.post("/api/lifelines", json={"game_id": game["id"], "kind": "5050"})
        self.assertEqual(created.status_code, 201)
        url = f"/api/lifelines/{created.get_json()['id']}"

        self.assertEqual(self.client.get(url).get_json()["kind"], "5050")
        patched = self.client.patch(url, json={"used_at": "2026-01-01T10:00:00+00:00"})
        self.assertEqual(patched.status_code, 200)
        self.assertTrue(patched.get_json()["used_at"].startswith("2026-01-01T10:00:00"))

        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_duplicate_lifeline_for_same_game_conflicts(self):
        game = self.create_game()
        payload = {"game_id": game["id"], "kind": "friend"}
        self.assertEqual(self.client.post("/api/lifelines", json=payload).status_code, 201)
        self.assertEqual(self.client.post("/api/lifelines", json=payload).status_code, 409)

    def test_validation(self):
        invalid = [
            {"kind": "5050"},
            {"game_id": 0, "kind": "5050"},
            {"game_id": 1, "kind": ""},
            {"game_id": 1, "kind": "x" * 51},
            {"game_id": 1, "kind": "5050", "used_at": "ayer"},
            {"game_id": 1, "kind": "5050", "extra": 1},
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/lifelines", json=payload).status_code, 400)

    def test_missing_lifeline_returns_404(self):
        self.assertEqual(self.client.get("/api/lifelines/999").status_code, 404)
        self.assertEqual(self.client.delete("/api/lifelines/999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
