# Multi-stage Dockerfile for Agentic F&O Backend
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd --create-home --shell /bin/bash agentic

# Copy Python packages from builder to user's home directory
COPY --from=builder /root/.local /home/agentic/.local

# Make sure scripts in .local are usable and owned by agentic user
RUN chown -R agentic:agentic /home/agentic/.local
ENV PATH=/home/agentic/.local/bin:$PATH

# Copy application code
COPY . .

# Change ownership of app directory
RUN chown -R agentic:agentic /app

# Switch to non-root user
USER agentic

# Set working directory to app
WORKDIR /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
