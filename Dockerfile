# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.7

FROM python:${PYTHON_VERSION}-slim as builder

LABEL fly_launch_runtime="flask"

WORKDIR /code

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:${PYTHON_VERSION}-slim

WORKDIR /code

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m myuser && \
    chown -R myuser:myuser /code
USER myuser

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "60", "run:app"]