FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /code

# Install dependencies from the same pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy your frontend code
COPY ./frontend /code/frontend

EXPOSE 8501

# Run Streamlit. We bind to 0.0.0.0 so it's accessible outside the container.
CMD ["streamlit", "run", "frontend/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]