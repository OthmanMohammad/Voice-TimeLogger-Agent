FROM python:3.9-slim-bullseye as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies - leveraging Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base as production

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup --system app && adduser --system --group app

# Create necessary directories with proper permissions
RUN mkdir -p /app/tmp/meeting_recordings \
    && mkdir -p /app/credentials || true \
    && chmod -R 777 /app/tmp \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Healthcheck to verify API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the API server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]