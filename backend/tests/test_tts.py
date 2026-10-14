from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from backend.routes import tts
from backend.tests.helpers import ApiTestCase


FAKE_WAV = b"RIFF0000WAVEfmt "


class TtsValidationTests(ApiTestCase):
    QUESTION_COUNT = 0

    def post(self, payload):
        return self.client.post("/api/tts", json=payload)

    def test_invalid_requests_are_rejected(self):
        invalid = {
            "sin texto": {},
            "texto vacío": {"text": "   "},
            "texto demasiado largo": {"text": "a" * (tts.MAX_TEXT_LENGTH + 1)},
            "texto no es cadena": {"text": 5},
            "idioma inválido": {"text": "Hola", "language": "fr"},
            "presentador inválido": {"text": "Hola", "presenter": "pikachu"},
            "campo desconocido": {"text": "Hola", "volume": 10},
        }
        for label, payload in invalid.items():
            with self.subTest(label):
                self.assertEqual(self.post(payload).status_code, 400)

    def test_every_presenter_has_both_voice_styles(self):
        self.assertEqual(set(tts.PIPER_STYLES), set(tts.ESPEAK_STYLES))
        self.assertEqual(set(tts.PIPER_STYLES), {"clasico", "terminator", "masterchief", "james", "cr7"})


class TtsEngineSelectionTests(ApiTestCase):
    QUESTION_COUNT = 0

    def post(self):
        return self.client.post("/api/tts", json={"text": "Hola", "presenter": "james", "language": "en"})

    def test_uses_piper_when_available(self):
        with mock.patch.object(tts, "synthesize_with_piper", return_value=FAKE_WAV) as piper, \
                mock.patch.object(tts, "synthesize_with_espeak") as espeak:
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        self.assertEqual(response.data, FAKE_WAV)
        piper.assert_called_once_with("Hola", "en", "james")
        espeak.assert_not_called()

    def test_falls_back_to_espeak(self):
        with mock.patch.object(tts, "synthesize_with_piper", return_value=None), \
                mock.patch.object(tts, "synthesize_with_espeak", return_value=FAKE_WAV) as espeak:
            response = self.post()
        self.assertEqual(response.status_code, 200)
        espeak.assert_called_once_with("Hola", "en", "james")

    def test_returns_503_without_any_engine(self):
        with mock.patch.object(tts, "synthesize_with_piper", return_value=None), \
                mock.patch.object(tts, "synthesize_with_espeak", return_value=None):
            self.assertEqual(self.post().status_code, 503)

    def test_returns_500_when_engine_fails(self):
        with mock.patch.object(tts, "synthesize_with_piper", return_value=None), \
                mock.patch.object(tts, "synthesize_with_espeak", side_effect=subprocess.TimeoutExpired("espeak", 15)):
            self.assertEqual(self.post().status_code, 500)

    def test_espeak_receives_text_through_stdin(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=FAKE_WAV)
        with mock.patch.object(tts.shutil, "which", return_value="/usr/bin/espeak-ng"), \
                mock.patch.object(tts.subprocess, "run", return_value=completed) as run:
            audio = tts.synthesize_with_espeak("-x peligro", "es", "cr7")
        self.assertEqual(audio, FAKE_WAV)
        args, kwargs = run.call_args
        self.assertNotIn("-x peligro", args[0])
        self.assertEqual(kwargs["input"], "-x peligro".encode("utf-8"))

    def test_espeak_missing_returns_none(self):
        with mock.patch.object(tts.shutil, "which", return_value=None):
            self.assertIsNone(tts.synthesize_with_espeak("Hola", "es", "clasico"))


@unittest.skipUnless(
    tts.load_piper_voice("es") is not None or tts.shutil.which("espeak-ng") or tts.shutil.which("espeak"),
    "No hay motor de voz instalado en este equipo",
)
class TtsRealEngineTests(ApiTestCase):
    QUESTION_COUNT = 0

    def test_real_engine_generates_wav_for_every_presenter(self):
        for presenter in tts.PIPER_STYLES:
            for language in ("es", "en"):
                with self.subTest(presenter=presenter, language=language):
                    response = self.client.post(
                        "/api/tts", json={"text": "Prueba", "presenter": presenter, "language": language}
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data[:4], b"RIFF")


if __name__ == "__main__":
    unittest.main()
