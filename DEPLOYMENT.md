# Deployment Guide - HR-RAG

A comprehensive guide for deploying HR-RAG in development and production environments.

---

## Prerequisites

### Required Software
- **Docker** (v20.10+) - [Install](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+) - Included with Docker Desktop
- **Git** - For cloning the repository

### Cloud Services
- **TiDB Cloud** account - [Sign up](https://tidb.cloud/) (free tier available)
- **LLM API Key** - At least one of:
  - OpenAI ([platform.openai.com](https://platform.openai.com/))
  - Anthropic Claude ([anthropic.com](https://www.anthropic.com/))
  - Google Gemini ([aistudio.google.com](https://aistudio.google.com/app/apikey))
  - Other supported providers (Kimi, GLM, MiniMax, Qwen, DeepSeek)

### Optional
- **Redis** - For production caching (included in docker-compose)
- **Domain name** - For production HTTPS setup
- **SSL Certificate** - For HTTPS termination

---

## Development Setup

### 1. Clone and Setup

```bash
git clone https://github.com/Arnutt-N/hr-rag.git
cd hr-rag
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your local settings:

```bash
# Required: Generate a secure JWT key
JWT_SECRET_KEY=$(openssl rand -hex 64)
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env

# Database (local TiDB for development)
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=hr_rag
MYSQL_PORT=4000

# LLM Provider (at least one)
OPENAI_API_KEY=your-openai-key-here

# Keep other defaults for development
```

### 3. Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# View logs to ensure everything started
docker-compose logs -f
```

### 4. Verify Health

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status":"ok","message":"HR-RAG API is running"}

# Frontend
curl http://localhost:3000
# Expected: HTML page loads

# Check service status
docker-compose ps
```

### 5. First-Time Setup

Once services are running:
1. Open http://localhost:3000 in browser
2. Register a new account
3. Create a project
4. Upload HR documents (PDF, TXT, MD, DOC, DOCX)
5. Start chatting with your documents

---

## Production Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                   (Nginx / CloudFlare)                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Reverse Proxy                          │
│                   (Nginx / Traefik)                         │
│                        :443 → :8000                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │ Frontend │        │ Backend  │        │  Redis   │
   │  (xN)    │◄──────│  (xN)    │◄──────│ Cluster  │
   └──────────┘        └──────────┘        └──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌──────────┐    ┌──────────┐
        │ Qdrant  │     │  TiDB    │    │   LLM    │
        │ Cluster │     │  Cloud   │    │ Providers│
        └─────────┘     └──────────┘    └──────────┘
```

### Step 1: Production Environment Variables

Create a production `.env` file:

```bash
# ============================================
# PRODUCTION ENVIRONMENT
# ============================================

# ⚠️ CRITICAL: Generate secure keys
JWT_SECRET_KEY=$(openssl rand -hex 64)

# Database - TiDB Cloud (Production)
TIDB_HOST=your-cluster.xxxx.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=your-username
TIDB_PASSWORD=your-secure-password
TIDB_DATABASE=hr_rag_prod

# Redis - Use managed Redis or cloud service
REDIS_URL=redis://your-redis-host:6379/0
REDIS_PASSWORD=your-redis-password

# Qdrant - Use Qdrant Cloud or self-hosted cluster
QDRANT_HOST=your-qdrant-cluster.cloud
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key

# CORS - Production domain only
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# LLM Provider
OPENAI_API_KEY=your-production-api-key

# Rate Limiting - Stricter for production
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_DAY=1000

# Admin Security
ADMIN_SESSION_TIMEOUT=86400        # 24 hours
ADMIN_MAX_LOGIN_ATTEMPTS=5
ADMIN_IP_BLOCK_DURATION=3600       # 1 hour
ADMIN_LOG_RETENTION_DAYS=90

# Logging
LOG_LEVEL=INFO
NODE_ENV=production
```

### Step 2: Security Checklist

Before deploying to production, verify:

- [ ] `JWT_SECRET_KEY` set to a strong 64+ character random value
- [ ] `CORS_ORIGINS` set to production domain only (no localhost)
- [ ] TiDB Cloud credentials configured with least-privilege access
- [ ] Redis password set (or use Redis Cloud with auth)
- [ ] Qdrant API key enabled (if using Qdrant Cloud)
- [ ] Rate limiting enabled and tested
- [ ] SSL/TLS enabled (via reverse proxy or cloud provider)
- [ ] Admin IP blocking enabled
- [ ] Log retention configured (90 days recommended)
- [ ] File upload restrictions in place (max size, allowed types)

### Step 3: Deploy with Docker Compose

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build --no-cache

# Start services
docker-compose -f docker-compose.yml up -d

# Verify deployment
docker-compose ps
curl https://your-domain.com/health
```

### Step 4: Reverse Proxy Setup (HTTPS)

#### Option A: Nginx

```nginx
# /etc/nginx/sites-available/hr-rag
server {
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
}

server {
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

#### Option B: Cloudflare

1. Point domain to Cloudflare
2. Enable "Proxy" mode
3. Create origin server certificate
4. Configure SSL/TLS to "Full" or "Strict"

### Step 5: Scaling Configuration

For high availability:

```yaml
# docker-compose.prod.yml (example)
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    
  frontend:
    deploy:
      replicas: 2
    
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your-password --appendonly yes
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

Apply with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Monitoring

### Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Backend | `GET /health` | `{"status":"ok"}` |
| Backend | `GET /health/ready` | `{"status":"ready","checks":{...}}` |
| Qdrant | `GET http://localhost:6333/health` | `{"status":"ok"}` |

### JSON Structured Logging

All logs are structured JSON for easy parsing:

```json
{
  "timestamp": "2026-03-07T12:00:00Z",
  "level": "INFO",
  "service": "backend",
  "event": "request",
  "method": "POST",
  "path": "/api/chat/sessions/1/messages",
  "status_code": 200,
  "duration_ms": 1500,
  "user_id": "user-123"
}
```

### Metrics Integration (Optional)

For Prometheus/Grafana integration:

```bash
# Enable metrics endpoint
METRICS_ENABLED=true
METRICS_PORT=9090
```

Add to Prometheus config:
```yaml
scrape_configs:
  - job_name: 'hr-rag-backend'
    static_configs:
      - targets: ['localhost:9090']
```

### Log Management

```bash
# View recent logs
docker-compose logs --tail=100 backend

# Follow logs in real-time
docker-compose logs -f backend

# Export logs for debugging
docker-compose logs backend > logs.txt
```

---

## Backup & Recovery

### Database Backup (TiDB Cloud)

```bash
# Using TiDB Cloud console or mydumper
# Recommended: Use TiDB Cloud automated backups

# Manual backup (CLI)
mysqldump -h $TIDB_HOST -P $TIDB_PORT -u $TIDB_USER -p $TIDB_DATABASE > backup.sql
```

### Vector Data Backup (Qdrant)

```bash
# Backup collections
curl -X POST http://localhost:6333/collections/hr_documents/snapshot

# Or use Qdrant Cloud backup feature
```

### Recovery Procedure

1. Stop services: `docker-compose down`
2. Restore database: `mysql -h $TIDB_HOST -u $TIDB_USER -p $TIDB_DATABASE < backup.sql`
3. Restore vector data if needed
4. Restart services: `docker-compose up -d`
5. Verify health: `curl http://localhost:8000/health`

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Backend won't start | Check `.env` file and logs: `docker-compose logs backend` |
| Database connection failed | Verify TiDB Cloud credentials and network access |
| Slow vector search | Check Qdrant resources, consider adding more nodes |
| Rate limit errors | Adjust `RATE_LIMIT_PER_MINUTE` in `.env` |
| CORS errors | Verify `CORS_ORIGINS` includes your frontend domain |
| WebSocket disconnected | Check reverse proxy WebSocket configuration |

### Health Check Commands

```bash
# Check all services
docker-compose ps

# Backend detailed health
curl http://localhost:8000/health/ready

# Database connection
docker-compose exec backend python -c "from app.database import engine; engine.connect()"

# Redis connection
docker-compose exec redis redis-cli ping

# Qdrant status
curl http://localhost:6333/health
```

---

## Support

- **Documentation**: Check `/docs` endpoint for API docs
- **Issues**: Create issue at https://github.com/Arnutt-N/hr-rag/issues
- **Logs**: Check `docker-compose logs -f` for detailed errors
