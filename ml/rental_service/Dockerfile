FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY ml/rental_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --retries 20 --timeout 120 -r /app/requirements.txt

COPY ml/rental_service /app/ml/rental_service

EXPOSE 8000

CMD ["sh", "-c", "uvicorn ml.rental_service.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
