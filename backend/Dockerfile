# Use Python 3.11+ for development
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy pyproject.toml for additional configuration
COPY pyproject.toml ./

# Copy source code
COPY . .

# Expose the API port
EXPOSE 8000

# Set environment variables for development
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command for development with hot reload
CMD ["python", "main.py"]