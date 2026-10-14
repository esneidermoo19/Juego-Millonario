from __future__ import annotations

import unittest

from backend.tests.helpers import ApiTestCase


class PlayerApiTests(ApiTestCase):
    def test_create_player_trims_name(self):
        response = self.client.post("/api/players", json={"name": "  Sofía  "})
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["name"], "Sofía")
        self.assertIn("id", body)
        self.assertIn("created_at", body)

    def test_create_player_rejects_invalid_names(self):
        for name in ["", "   ", None, 123, "x" * 101]:
            with self.subTest(name=name):
                response = self.client.post("/api/players", json={"name": name})
                self.assertEqual(response.status_code, 400)

    def test_create_player_rejects_unknown_fields(self):
        response = self.client.post("/api/players", json={"name": "Ana", "admin": True})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown fields", response.get_json()["error"])

    def test_create_player_requires_json(self):
        response = self.client.post("/api/players", data="name=Ana")
        self.assertEqual(response.status_code, 415)

    def test_name_with_html_is_stored_as_plain_text(self):
        name = "<script>alert(1)</script>"
        player = self.create_player(name)
        self.assertEqual(player["name"], name)

    def test_list_and_get_players(self):
        first = self.create_player("Ana")
        second = self.create_player("Luis")
        players = self.client.get("/api/players").get_json()
        self.assertEqual([player["id"] for player in players], [first["id"], second["id"]])
        response = self.client.get(f"/api/players/{second['id']}")
        self.assertEqual(response.get_json()["name"], "Luis")

    def test_get_missing_player_returns_404(self):
        response = self.client.get("/api/players/9999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "Player not found")

    def test_update_player_name(self):
        player = self.create_player("Ana")
        for method in (self.client.put, self.client.patch):
            with self.subTest(method=method.__name__):
                response = method(f"/api/players/{player['id']}", json={"name": "Ana María"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json()["name"], "Ana María")

    def test_update_player_validation(self):
        player = self.create_player("Ana")
        self.assertEqual(self.client.patch(f"/api/players/{player['id']}", json={}).status_code, 400)
        self.assertEqual(self.client.patch(f"/api/players/{player['id']}", json={"name": ""}).status_code, 400)
        self.assertEqual(self.client.patch("/api/players/9999", json={"name": "X"}).status_code, 404)

    def test_delete_player_also_deletes_games(self):
        game = self.create_game("Borrar")
        response = self.client.delete(f"/api/players/{game['player_id']}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get(f"/api/players/{game['player_id']}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/games/{game['id']}").status_code, 404)

    def test_delete_missing_player_returns_404(self):
        self.assertEqual(self.client.delete("/api/players/9999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
