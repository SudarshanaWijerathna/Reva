FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-backend.txt /app/requirements-backend.txt
RUN pip install --upgrade pip && \
    pip install --retries 20 --timeout 120 -r /app/requirements-backend.txt

COPY . /app

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
