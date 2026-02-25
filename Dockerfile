FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRACKER_CONTAINER=1 \
    TRACKER_DB_PATH=/app/data/tracker.db \
    TRACKER_SOURCES_FILE=/app/sources.md \
    TRACKER_POLL_SECONDS=900 \
    TRACKER_MIN_POLL_SECONDS=600

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY tracker /app/tracker
COPY docs /app/docs
COPY sources.md /app/sources.md

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

RUN mkdir -p /app/data

EXPOSE 8787
CMD ["python", "-m", "tracker.web"]
