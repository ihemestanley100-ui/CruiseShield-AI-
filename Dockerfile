# Image build from the dev sandbox is blocked (docker engine permission denied
# on npipe). Render builds server-side on Blueprint deploy (see render.yaml),
# or build locally with: docker build -t cruiseshield-ai .
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/srv/data

WORKDIR /srv/app
COPY requirements.txt requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY app/ app/
COPY templates/ templates/
COPY static/ static/

EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
