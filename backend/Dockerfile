FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway/Render iniettano $PORT a runtime — shell form per espandere la variabile
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
