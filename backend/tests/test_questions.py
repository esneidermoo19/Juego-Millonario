from __future__ import annotations

import unittest

from backend.models import Question
from backend.services.question_translations import ENGLISH_QUESTIONS
from backend.tests.helpers import ApiTestCase


VALID_QUESTION = {
    "text": "¿Cuánto es 2 + 2?",
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6",
    "correct_option": "b",
    "category": "Matemáticas",
    "difficulty": 1,
}


class QuestionCrudTests(ApiTestCase):
    QUESTION_COUNT = 0

    def test_create_question_normalizes_correct_option(self):
        response = self.client.post("/api/questions", json=VALID_QUESTION)
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["correct_option"], "B")
        self.assertEqual(body["category"], "Matemáticas")

    def test_create_question_requires_all_fields(self):
        incomplete = {key: value for key, value in VALID_QUESTION.items() if key != "option_d"}
        response = self.client.post("/api/questions", json=incomplete)
        self.assertEqual(response.status_code, 400)
        self.assertIn("option_d", response.get_json()["error"])

    def test_create_question_validation(self):
        invalid_cases = {
            "texto vacío": {"text": "  "},
            "opción correcta inválida": {"correct_option": "E"},
            "opción demasiado larga": {"option_a": "x" * 501},
            "dificultad no entera": {"difficulty": "alta"},
            "dificultad booleana": {"difficulty": True},
            "categoría demasiado larga": {"category": "x" * 101},
            "campo desconocido": {"secret": 1},
        }
        for label, override in invalid_cases.items():
            with self.subTest(label):
                response = self.client.post("/api/questions", json={**VALID_QUESTION, **override})
                self.assertEqual(response.status_code, 400)

    def test_get_update_and_delete_question(self):
        question = self.client.post("/api/questions", json=VALID_QUESTION).get_json()
        url = f"/api/questions/{question['id']}"

        self.assertEqual(self.client.get(url).get_json()["text"], VALID_QUESTION["text"])

        patched = self.client.patch(url, json={"difficulty": 5})
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.get_json()["difficulty"], 5)

        self.assertEqual(self.client.put(url, json={"text": "Solo texto"}).status_code, 400)
        replaced = self.client.put(url, json={**VALID_QUESTION, "text": "Nueva"})
        self.assertEqual(replaced.get_json()["text"], "Nueva")

        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_missing_question_returns_404(self):
        self.assertEqual(self.client.get("/api/questions/999").status_code, 404)
        self.assertEqual(self.client.patch("/api/questions/999", json={"difficulty": 1}).status_code, 404)
        self.assertEqual(self.client.delete("/api/questions/999").status_code, 404)

    def test_list_questions(self):
        self.client.post("/api/questions", json=VALID_QUESTION)
        self.client.post("/api/questions", json={**VALID_QUESTION, "text": "Otra"})
        self.assertEqual(len(self.client.get("/api/questions").get_json()), 2)


class GameQuestionsTests(ApiTestCase):
    def test_game_questions_hide_the_correct_answer(self):
        game = self.create_game()
        response = self.client.get(f"/api/questions/game?game_id={game['id']}")
        self.assertEqual(response.status_code, 200)
        questions = response.get_json()["questions"]
        self.assertEqual(len(questions), 15)
        for question in questions:
            self.assertNotIn("correct_option", question)
            self.assertEqual(set(question["options"]), {"A", "B", "C", "D"})

    def test_game_questions_in_english_use_translations(self):
        game = self.create_game()
        response = self.client.get(f"/api/questions/game?game_id={game['id']}&language=en")
        self.assertEqual(response.status_code, 200)
        first = response.get_json()["questions"][0]
        english_texts = {text for text, _ in ENGLISH_QUESTIONS}
        self.assertIn(first["question"], english_texts)

    def test_same_option_order_in_both_languages(self):
        game = self.create_game()
        spanish = self.client.get(f"/api/questions/game?game_id={game['id']}&language=es").get_json()
        english = self.client.get(f"/api/questions/game?game_id={game['id']}&language=en").get_json()
        for es_question, en_question in zip(spanish["questions"], english["questions"]):
            self.assertEqual(es_question["id"], en_question["id"])
            source = ENGLISH_QUESTIONS[es_question["difficulty"] - 1][1]
            for letter in "ABCD":
                # "Correcta N" es la opción original A; "Incorrecta X N" es la opción original X.
                words = es_question["options"][letter].split()
                original_letter = "A" if words[0] == "Correcta" else words[1]
                self.assertEqual(en_question["options"][letter], source["ABCD".index(original_letter)])

    def test_game_questions_validation(self):
        self.assertEqual(self.client.get("/api/questions/game").status_code, 400)
        self.assertEqual(self.client.get("/api/questions/game?game_id=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/questions/game?game_id=-1").status_code, 400)
        self.assertEqual(self.client.get("/api/questions/game?game_id=999").status_code, 404)
        game = self.create_game()
        self.assertEqual(
            self.client.get(f"/api/questions/game?game_id={game['id']}&language=fr").status_code, 400
        )

    def test_english_fails_when_a_question_has_no_translation(self):
        with self.session_factory() as session:
            for question in session.query(Question).all():
                question.difficulty = None
            session.commit()
        game = self.create_game()
        response = self.client.get(f"/api/questions/game?game_id={game['id']}&language=en")
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
