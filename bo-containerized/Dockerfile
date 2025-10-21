# Dockerfile for Containerized BO HITL Workflow
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the BO workflow files and setup script
COPY complete_workflow/ ./complete_workflow/
COPY setup.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Configure Prefect to connect to host machine Prefect server
ENV PREFECT_API_URL=http://host.docker.internal:4200/api

# Run as Prefect worker to execute deployments
CMD ["prefect", "worker", "start", "--pool", "docker-pool"]