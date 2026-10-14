#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python 3. Instálalo desde https://www.python.org/downloads/ y vuelve a intentarlo."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -r backend/requirements.txt

# Voces de los presentadores (solo la primera vez). Si falla, el juego usa una voz de respaldo.
if [ ! -f "backend/tts_voices/en_US-ryan-medium.onnx" ]; then
  echo "Descargando voces de los presentadores (~126 MB)..."
  .venv/bin/python -m piper.download_voices --data-dir backend/tts_voices es_MX-ald-medium en_US-ryan-medium \
    || echo "No se pudieron descargar las voces; se usará la voz de respaldo."
fi

exec .venv/bin/python -m backend.app
