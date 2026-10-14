from __future__ import annotations

import re
import unittest
from pathlib import Path

from backend.tests.helpers import ApiTestCase


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
PAGES = ["index.html", "game.html", "results.html", "ranking.html"]


class AppTests(ApiTestCase):
    QUESTION_COUNT = 0

    def test_root_serves_home_page(self):
        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"<html", response.data.lower())

    def test_all_pages_are_served(self):
        for page in PAGES:
            with self.subTest(page=page), self.client.get(f"/{page}") as response:
                self.assertEqual(response.status_code, 200)

    def test_every_local_file_referenced_by_pages_exists(self):
        for page in PAGES:
            html = (FRONTEND / page).read_text(encoding="utf-8")
            for reference in re.findall(r'(?:src|href|srcset)="([^"#:]+)"', html):
                with self.subTest(page=page, reference=reference):
                    self.assertTrue((FRONTEND / reference).exists())

    def test_every_presenter_has_images(self):
        for presenter in ["clasico", "terminator", "masterchief", "james", "cr7"]:
            for extension in ("png", "webp"):
                with self.subTest(presenter=presenter, extension=extension):
                    self.assertTrue((FRONTEND / "assets" / "images" / f"presentador-{presenter}.{extension}").exists())

    def test_unknown_api_route_returns_json_404(self):
        response = self.client.get("/api/no-existe")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_wrong_method_returns_json_405(self):
        response = self.client.delete("/api/ranking")
        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.get_json())

    def test_cors_headers_are_present(self):
        response = self.client.get("/api/ranking")
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")


if __name__ == "__main__":
    unittest.main()
