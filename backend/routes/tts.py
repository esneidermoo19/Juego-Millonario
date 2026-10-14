from __future__ import annotations

import io
import shutil
import subprocess
import threading
import wave
from pathlib import Path

from flask import Blueprint, Response, jsonify

from .common import json_body, unknown_fields


tts_bp = Blueprint("tts", __name__)
TTS_FIELDS = {"text", "language", "presenter"}
MAX_TEXT_LENGTH = 600

# Voces neuronales de Piper (descargadas en backend/tts_voices por iniciar_juego).
VOICES_DIR = Path(__file__).resolve().parent.parent / "tts_voices"
PIPER_VOICES = {"es": "es_MX-ald-medium", "en": "en_US-ryan-medium"}
# (tono, duración): tono < 1 es más grave, duración > 1 es más lento.
PIPER_STYLES = {
    "clasico": (1.0, 1.0),
    "terminator": (0.82, 1.1),
    "masterchief": (0.9, 1.05),
    "james": (1.08, 0.95),
    "cr7": (0.94, 0.9),
}

# Respaldo con espeak-ng: variante de voz, tono (0-99) y velocidad (palabras por minuto).
ESPEAK_VOICES = {"es": "es-419", "en": "en-us"}
ESPEAK_STYLES = {
    "clasico": ("m1", 45, 150),
    "terminator": ("m1", 25, 140),
    "masterchief": ("m3", 35, 145),
    "james": ("m2", 60, 155),
    "cr7": ("m4", 40, 165),
}

_loaded_voices: dict[str, object] = {}
_voices_lock = threading.Lock()


def load_piper_voice(language: str):
    """Carga la voz una sola vez; devuelve None si Piper o el modelo no están disponibles."""
    with _voices_lock:
        if language in _loaded_voices:
            return _loaded_voices[language]
        voice = None
        model = VOICES_DIR / f"{PIPER_VOICES[language]}.onnx"
        if model.exists():
            try:
                from piper import PiperVoice

                voice = PiperVoice.load(str(model))
            except Exception:
                voice = None
        _loaded_voices[language] = voice
        return voice


def synthesize_with_piper(text: str, language: str, presenter: str) -> bytes | None:
    voice = load_piper_voice(language)
    if voice is None:
        return None
    from piper import SynthesisConfig

    pitch, duration = PIPER_STYLES[presenter]
    # Se sintetiza más rápido/lento y luego se cambia la frecuencia de muestreo:
    # así se cambia el tono sin alterar la duración final.
    raw = io.BytesIO()
    with wave.open(raw, "wb") as writer:
        voice.synthesize_wav(text, writer, syn_config=SynthesisConfig(length_scale=duration * pitch))
    raw.seek(0)
    with wave.open(raw, "rb") as reader:
        params = reader.getparams()
        frames = reader.readframes(params.nframes)
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(params.nchannels)
        writer.setsampwidth(params.sampwidth)
        writer.setframerate(round(params.framerate * pitch))
        writer.writeframes(frames)
    return output.getvalue()


def synthesize_with_espeak(text: str, language: str, presenter: str) -> bytes | None:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak is None:
        return None
    variant, pitch, speed = ESPEAK_STYLES[presenter]
    # El texto va por stdin para que nunca se interprete como opción de línea de comandos.
    result = subprocess.run(
        [espeak, "-v", f"{ESPEAK_VOICES[language]}+{variant}",
         "-p", str(pitch), "-s", str(speed), "-a", "180", "-g", "3", "--stdout"],
        input=text.encode("utf-8"),
        capture_output=True,
        timeout=15,
        check=True,
    )
    return result.stdout


@tts_bp.post("")
def synthesize():
    """Devuelve un WAV con el texto leído por la voz del presentador elegido."""
    data, error = json_body()
    if error:
        return error
    assert data is not None
    invalid = unknown_fields(data, TTS_FIELDS)
    if invalid:
        return jsonify(error=f"Unknown fields: {', '.join(sorted(invalid))}"), 400
    text = data.get("text")
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_LENGTH:
        return jsonify(error=f"text must be a non-empty string of at most {MAX_TEXT_LENGTH} characters"), 400
    language = data.get("language", "es")
    if language not in PIPER_VOICES:
        return jsonify(error="language must be es or en"), 400
    presenter = data.get("presenter", "clasico")
    if presenter not in PIPER_STYLES:
        return jsonify(error="Unknown presenter"), 400

    text = text.strip()
    try:
        audio = synthesize_with_piper(text, language, presenter)
        if audio is None:
            audio = synthesize_with_espeak(text, language, presenter)
    except (subprocess.SubprocessError, OSError, ValueError):
        return jsonify(error="Could not generate speech"), 500
    if audio is None:
        return jsonify(error="Text-to-speech is not available on this server"), 503
    return Response(audio, mimetype="audio/wav")
