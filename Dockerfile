# Alternative Dockerfile using official UV image
# Use this if the main Dockerfile has issues

# Stage 1: Use UV image for dependency installation
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set work directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .
COPY pyproject.toml* .
COPY uv.lock* .

# Install dependencies
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Create final image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directory for database and logs
RUN mkdir -p /app/data /app/logs

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
