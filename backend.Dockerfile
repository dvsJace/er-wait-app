# Use a slim 2026-ready Python image
FROM python:3.12-slim

# Prevent Python from buffering logs (important for seeing your triage logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

# Install system dependencies for SQLite and general builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install your project using the pyproject.toml
COPY pyproject.toml .
# If you have a lock file, uncomment the next line:
# COPY poetry.lock* . 

RUN pip install --no-cache-dir .

# Copy your backend code
COPY ./app /code/app

# Create a persistent data directory for your AHS cache
RUN mkdir -p /code/data

EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "app.fastapi.server:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]