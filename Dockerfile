FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    WEB_CONCURRENCY=4 \
    DATABASE_URL=sqlite:///backend/instance/millionaire.db

WORKDIR /app

# Motor de voz para que los presentadores lean las preguntas (/api/tts).
RUN apt-get update \
    && apt-get install -y --no-install-recommends espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
COPY backend/requirements-docker.txt backend/requirements-docker.txt
RUN python -m pip install --no-cache-dir -r backend/requirements-docker.txt

COPY backend/ backend/
COPY frontend/ frontend/
RUN mkdir -p backend/instance \
    && python -m piper.download_voices --data-dir backend/tts_voices es_MX-ald-medium en_US-ryan-medium

EXPOSE 5000

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-1} --threads 4 --access-logfile - --error-logfile - 'backend.app:create_app()'"]
