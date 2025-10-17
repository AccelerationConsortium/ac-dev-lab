# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy our application code
COPY hello.py .
COPY index.html .

# Set environment variable
ENV PYTHONPATH=/app

# Expose port (for documentation - doesn't actually open it)
EXPOSE 8000

# Default command when container starts
CMD ["python", "hello.py"]