# ============================================
# Smart Companion - Multi-stage Dockerfile
# Neuro-Inclusive Energy-Adaptive Micro-Wins System
# ============================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source files
COPY frontend/ ./

# Build the frontend
RUN npm run build

# ============================================
# Stage 2: Python Backend with Frontend Static Files
# ============================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENCRYPTION_KEY="" \
    DATABASE_URL="sqlite:///./smart_companion.db"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create static directory and copy frontend build
RUN mkdir -p /app/static
COPY --from=frontend-builder /app/frontend/dist/ /app/static/

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
