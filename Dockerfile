# ============================================
# Smart Companion - Optimized Multi-stage Dockerfile
# Neuro-Inclusive Energy-Adaptive Micro-Wins System
# ============================================

# Stage 1: Build React Frontend with tree-shaking
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first (better layer caching)
COPY frontend/package.json frontend/package-lock.json* ./

# Install ALL dependencies (dev deps needed for build)
RUN npm ci && npm cache clean --force

# Copy source files
COPY frontend/ ./

# Build with production optimizations
ENV NODE_ENV=production
RUN npm run build

# ============================================
# Stage 2: Python dependencies builder
# ============================================
FROM python:3.11-alpine AS python-builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete

# ============================================
# Stage 3: Minimal production image
# ============================================
FROM python:3.11-alpine AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install only runtime dependencies (curl for healthcheck)
RUN apk add --no-cache curl libffi && \
    addgroup -S appuser && adduser -S appuser -G appuser

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv

# Copy backend code (excluding dev files)
COPY backend/*.py backend/routers backend/services ./
COPY backend/routers/ ./routers/
COPY backend/services/ ./services/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist/ /app/static/

# Create data directory and set permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
