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

# Configure Slack webhook (you MUST override this when running)
ENV SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Configure Prefect to connect to external server (replace with your host IP)
ENV PREFECT_API_URL=http://YOUR_HOST_IP:4200/api

# Default command - you can override this when running
CMD ["python", "complete_workflow/bo_hitl_slack_tutorial.py"]