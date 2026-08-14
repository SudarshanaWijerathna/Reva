# Standard slim Python 3.10 image for Google Cloud Run & standard cloud containers
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better Docker layer caching)
COPY requirements-backend.txt /app/requirements-backend.txt
RUN pip install --upgrade pip && \
    pip install --retries 20 --timeout 120 -r /app/requirements-backend.txt

# Copy application source
COPY backend /app/backend
COPY ml /app/ml
COPY Sentiment /app/Sentiment
COPY data /app/data
COPY scripts /app/scripts
COPY init_admin.py /app/init_admin.py

EXPOSE 8000

# Healthcheck — lets Docker / Cloud Run know the app is ready.
# Tries /health every 30s; marks unhealthy after 3 consecutive failures.
# start-period=90s accounts for TensorFlow + PyTorch model loading (~45-60s).
# Uses wget so that the $PORT shell variable is correctly expanded at runtime
# (Cloud Run sets $PORT dynamically, usually to 8080).
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
