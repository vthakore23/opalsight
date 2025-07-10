# Backend Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies with better error handling
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    pkg-config \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory for database
RUN mkdir -p instance

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000

# Create non-root user
RUN useradd -m -u 1000 opalsight && chown -R opalsight:opalsight /app
USER opalsight

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "4", "--timeout", "120", "run:app"] 