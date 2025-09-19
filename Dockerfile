FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects PORT at runtime; keep a default for local dev
ENV PORT=8000

# Start the RQ worker in background, then the API in foreground
CMD sh -c "python worker.py & uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
