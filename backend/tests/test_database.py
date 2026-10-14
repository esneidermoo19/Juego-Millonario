from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend.app import create_app
from backend.database import STARTER_QUESTIONS
from backend.models import Question
from backend.services.question_translations import ENGLISH_QUESTIONS


DEFAULT_DATABASE_URL = "sqlite:///backend/instance/millionaire.db"


class QuestionBankTests(unittest.TestCase):
    def test_bank_has_one_hundred_unique_questions(self):
        self.assertEqual(len(STARTER_QUESTIONS), 100)
        self.assertEqual(len({question[0] for question in STARTER_QUESTIONS}), 100)

    def test_every_question_is_well_formed(self):
        for text, a, b, c, d, answer in STARTER_QUESTIONS:
            with self.subTest(text=text):
                self.assertTrue(text.strip())
                self.assertEqual(len({a, b, c, d}), 4)
                self.assertIn(answer, "ABCD")

    def test_correct_answers_are_spread_across_letters(self):
        answers = [question[5] for question in STARTER_QUESTIONS]
        for letter in "ABCD":
            self.assertGreaterEqual(answers.count(letter), 20)

    def test_every_question_has_an_english_translation(self):
        self.assertEqual(len(ENGLISH_QUESTIONS), len(STARTER_QUESTIONS))
        for (es_text, *es_options), (en_text, en_options) in zip(STARTER_QUESTIONS, ENGLISH_QUESTIONS):
            with self.subTest(text=es_text):
                self.assertTrue(en_text.strip())
                self.assertEqual(len(en_options), 4)
                self.assertEqual(len(set(en_options)), 4)


class StarterSeedTests(unittest.TestCase):
    """La siembra automática solo se hace con la URL por defecto (ruta relativa al directorio actual)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        Path("backend/instance").mkdir(parents=True)
        self.apps = []

    def tearDown(self):
        for app in self.apps:
            app.extensions["database_engine"].dispose()
        os.chdir(self.previous_cwd)
        self.temp_dir.cleanup()

    def start_app(self):
        app = create_app({"TESTING": True, "DATABASE_URL": DEFAULT_DATABASE_URL})
        self.apps.append(app)
        return app

    def stored_questions(self, app):
        with app.extensions["database_session_factory"]() as session:
            return session.query(Question).order_by(Question.difficulty).all()

    def test_first_start_loads_the_whole_bank(self):
        questions = self.stored_questions(self.start_app())
        self.assertEqual([question.text for question in questions], [row[0] for row in STARTER_QUESTIONS])

    def test_restarting_does_not_duplicate_questions(self):
        self.start_app()
        self.assertEqual(len(self.stored_questions(self.start_app())), 100)

    def test_old_bank_questions_are_replaced(self):
        app = self.start_app()
        with app.extensions["database_session_factory"]() as session:
            old = session.query(Question).filter_by(difficulty=1).one()
            old.text = "Pregunta antigua"
            old.correct_option = "D"
            session.commit()

        questions = self.stored_questions(self.start_app())
        self.assertEqual(len(questions), 100)
        self.assertEqual(questions[0].text, STARTER_QUESTIONS[0][0])
        self.assertEqual(questions[0].correct_option, STARTER_QUESTIONS[0][5])


if __name__ == "__main__":
    unittest.main()
