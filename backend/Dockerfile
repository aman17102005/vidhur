FROM python:3.12-slim

# Tesseract is a system package: this is why the backend deploys as Docker on Render.
# tesseract-ocr-hin adds Hindi (Devanagari) text recognition next to English.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_THREAD_LIMIT=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

RUN useradd --create-home --uid 10001 vidhur
USER vidhur

# --no-access-log: request lines are never logged. Render provides $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --no-access-log"]
