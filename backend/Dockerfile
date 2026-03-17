# TechBank.ai Backend - FastAPI
FROM python:3.11-slim

WORKDIR /app

# Install system deps (psycopg2, gosu for non-root run)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (pywin32 is Windows-only, skipped on Linux)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create uploads directory with correct ownership (no 777)
RUN mkdir -p uploads/resumes uploads/jd && chown -R appuser:appuser /app

# Entrypoint fixes volume ownership and runs gunicorn as appuser
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
