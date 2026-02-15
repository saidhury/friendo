# Smart Companion - Deployment Guide

This guide covers deploying the Smart Companion application in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment (Recommended)](#docker-deployment-recommended)
- [Manual Deployment](#manual-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- **Docker** 20.10+ and **Docker Compose** 2.0+ (for containerized deployment)
- **Python** 3.11+ (for manual deployment)
- **Node.js** 20+ and **npm** 10+ (for frontend build)
- **Google Gemini API Key** (required for LLM features)

### Optional
- **OpenAI API Key** (fallback LLM provider)
- **PostgreSQL** 14+ (for production database, SQLite used by default)

---

## Environment Configuration

### 1. Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

### 2. Required Variables

```env
# LLM Configuration (at least one required)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional fallback

# Security (MUST change in production)
ENCRYPTION_KEY=your-32-character-encryption-key!

# Environment
ENVIRONMENT=production  # or 'development'
```

### 3. Optional Variables

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4  # Number of Gunicorn workers

# CORS (comma-separated origins)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (default: SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/smartcompanion

# Rate Limiting
RATE_LIMIT=100  # Requests per minute per IP

# Image Upload
MAX_IMAGE_SIZE=10485760  # 10MB in bytes
```

---

## Docker Deployment (Recommended)

### Quick Start

```bash
# Build and start the application
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at `http://localhost:8000`

### Production Docker Compose

Create a `docker-compose.prod.yml` for production:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - WORKERS=4
    volumes:
      - app_data:/app/data
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  app_data:
```

Run with:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Building the Image Separately

```bash
# Build
docker build -t smart-companion:latest .

# Run
docker run -d \
  --name smart-companion \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e ENCRYPTION_KEY=your_encryption_key \
  -e ENVIRONMENT=production \
  -v smart_companion_data:/app/data \
  smart-companion:latest
```

---

## Manual Deployment

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key
export ENCRYPTION_KEY=your_encryption_key
export ENVIRONMENT=production

# Run with Gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Or run with Uvicorn (development)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# The built files are in dist/ - serve with any static file server
```

### Serving Frontend with Nginx

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend static files
    location / {
        root /var/www/smart-companion/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## Cloud Deployment

### Azure Container Apps

```bash
# Login to Azure
az login

# Create resource group
az group create --name smart-companion-rg --location eastus

# Create Container Apps environment
az containerapp env create \
  --name smart-companion-env \
  --resource-group smart-companion-rg \
  --location eastus

# Deploy container
az containerapp create \
  --name smart-companion \
  --resource-group smart-companion-rg \
  --environment smart-companion-env \
  --image your-registry/smart-companion:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    GEMINI_API_KEY=secretref:gemini-key \
    ENCRYPTION_KEY=secretref:encryption-key \
    ENVIRONMENT=production
```

### AWS ECS / Fargate

1. Push image to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker tag smart-companion:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/smart-companion:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/smart-companion:latest
```

2. Create ECS task definition and service using AWS Console or CLI.

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/YOUR_PROJECT/smart-companion

# Deploy
gcloud run deploy smart-companion \
  --image gcr.io/YOUR_PROJECT/smart-companion \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=your_key,ENVIRONMENT=production" \
  --set-secrets "ENCRYPTION_KEY=encryption-key:latest"
```

### Railway / Render / Fly.io

These platforms support Docker deployments. Simply connect your GitHub repository and configure environment variables in their dashboard.

---

## Monitoring & Logging

### Application Logs

Logs are output to stdout/stderr and can be captured by Docker or your orchestration platform.

**Log Levels:**
- `DEBUG`: Detailed debugging information (development only)
- `INFO`: General operational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages

Set log level via environment:
```env
LOG_LEVEL=INFO
```

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### Metrics (Optional)

For production monitoring, consider adding:
- **Prometheus** metrics endpoint
- **Application Insights** (Azure)
- **CloudWatch** (AWS)
- **Cloud Monitoring** (GCP)

---

## Troubleshooting

### Common Issues

#### 1. Container fails to start

```bash
# Check logs
docker-compose logs app

# Common causes:
# - Missing GEMINI_API_KEY
# - Invalid ENCRYPTION_KEY (must be 32 characters)
# - Port 8000 already in use
```

#### 2. API returns 500 errors

```bash
# Check if LLM API keys are valid
curl -X POST http://localhost:8000/tasks/decompose \
  -H "Content-Type: application/json" \
  -d '{"goal": "test task"}'

# Check application logs for detailed errors
```

#### 3. Frontend can't connect to backend

- Verify CORS_ORIGINS includes your frontend domain
- Check if backend is running: `curl http://localhost:8000/health`
- Verify network/firewall rules allow traffic

#### 4. Database errors

```bash
# For SQLite - check file permissions
ls -la *.db

# For PostgreSQL - verify connection string
# DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Performance Tuning

```env
# Increase workers for higher traffic
WORKERS=8

# Adjust based on CPU cores (recommended: 2-4 × CPU cores)
```

### Security Checklist

- [ ] Change default ENCRYPTION_KEY
- [ ] Use HTTPS in production (use reverse proxy like Nginx)
- [ ] Set restrictive CORS_ORIGINS
- [ ] Keep API keys in secure secrets manager
- [ ] Enable rate limiting
- [ ] Regular security updates for dependencies

---

## Support

For issues and feature requests, please open an issue on the GitHub repository.
