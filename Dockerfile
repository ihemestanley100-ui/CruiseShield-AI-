# Local build verified 2026-11-02 (escalated shell; engine reachable):
#   docker build -t cruiseshield-ai .
# Render also builds server-side on Blueprint deploy (see render.yaml).
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
RUN mkdir -p /srv/data \
    && useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /srv/app /srv/data
USER appuser

EXPOSE 8000
# R17: probe ${PORT} (dynamic on Render), not hardcoded 8000. Exec form:
# urlopen failure raises -> nonzero exit; no shell operators needed.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('PORT','8000'),timeout=4)"
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
