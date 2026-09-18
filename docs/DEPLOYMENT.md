# SANCHAY IAS - Deployment Guide

## Overview

This guide covers deploying SANCHAY IAS to production environments.

---

## 🏗️ Pre-Deployment Checklist

### Code Quality
- [ ] All tests pass: `pytest`
- [ ] No linting errors: `flake8 backend/`
- [ ] Code is formatted: `black backend/`
- [ ] Type checking: `mypy backend/`

### Configuration
- [ ] `.env` file configured for production
- [ ] `DEBUG=False` 
- [ ] `API_RELOAD=False`
- [ ] CORS origins configured correctly
- [ ] Database backups configured

### Security
- [ ] No hardcoded secrets in code
- [ ] HTTPS enabled (frontend)
- [ ] API rate limiting configured
- [ ] Input validation in place

---

## 🖥️ Deployment Options

### Option 1: Linux/Unix with Systemd (Recommended)

#### 1. Create systemd service file

```ini
# /etc/systemd/system/sanchay-api.service
[Unit]
Description=SANCHAY API Service
After=network.target

[Service]
Type=notify
User=sanchay
WorkingDirectory=/opt/sanchay_ias
Environment="PATH=/opt/sanchay_ias/venv/bin"
ExecStart=/opt/sanchay_ias/venv/bin/python -m backend.api_server
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Start service

```bash
sudo systemctl daemon-reload
sudo systemctl start sanchay-api
sudo systemctl enable sanchay-api
sudo systemctl status sanchay-api
```

### Option 2: Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Environment
ENV API_HOST=0.0.0.0
ENV API_PORT=8001

# Initialize database on startup
RUN python scripts/init_local_db.py

# Run API
CMD ["python", "-m", "backend.api_server"]
```

#### Build & Run

```bash
docker build -t sanchay-ias:latest .
docker run -p 8001:8001 \
  -e API_PORT=8001 \
  -e CORS_ORIGINS="https://yourdomain.com" \
  -v sanchay_data:/app/data \
  sanchay-ias:latest
```

### Option 3: Gunicorn + Nginx

#### 1. Create Gunicorn config

```python
# gunicorn_config.py
bind = "127.0.0.1:8001"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
timeout = 30
```

#### 2. Start with Gunicorn

```bash
gunicorn -c gunicorn_config.py backend.api_server:app
```

#### 3. Nginx reverse proxy config

```nginx
upstream sanchay_api {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://sanchay_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static frontend
    location /app {
        alias /opt/sanchay_ias/frontend;
        try_files $uri $uri/ =404;
    }
}
```

---

## 📊 Database Management

### Backup

```bash
# Backup database
cp data/sanchay_local.db data/sanchay_local.db.backup.$(date +%Y%m%d_%H%M%S)

# Or use SQLite dump
sqlite3 data/sanchay_local.db ".dump" > backup.sql
```

### Restore

```bash
sqlite3 data/sanchay_local.db < backup.sql
```

---

## 🔒 Security Best Practices

### 1. Environment Secrets

Never commit `.env` file:

```bash
# Generate strong API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Store in .env
echo "API_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

### 2. HTTPS/SSL

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ...
}
```

### 3. Rate Limiting

```python
# Add to api_server.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/health")
@limiter.limit("100/minute")
async def health_check():
    return {"status": "ok"}
```

---

## 📈 Monitoring & Logging

### 1. Application Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sanchay.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Monitor Service Health

```bash
# Check API health
curl http://localhost:8001/health

# Monitor logs
tail -f logs/sanchay.log
```

### 3. Performance Monitoring

Use tools like:
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **New Relic** - APM
- **DataDog** - Monitoring

---

## 🚀 Scaling Considerations

### Horizontal Scaling

1. **API Server Instances**
   - Run multiple API instances on different ports
   - Use load balancer (Nginx, HAProxy)
   - Share database across instances

2. **Database Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_client_advisor ON clients(advisor_id);
   CREATE INDEX idx_goal_client ON goals(client_id);
   CREATE INDEX idx_transaction_date ON transactions(transaction_date);
   ```

3. **Caching**
   - Add Redis for session/data cache
   - Cache API responses
   - Clear on data updates

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy SANCHAY

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
      - run: flake8 backend/
      
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          # Deploy commands here
          ssh user@server 'cd /opt/sanchay_ias && git pull && systemctl restart sanchay-api'
```

---

## 🆘 Troubleshooting Deployment

### Service Won't Start

```bash
# Check logs
journalctl -u sanchay-api -n 50

# Check port
sudo netstat -tlnp | grep 8001

# Test directly
python -m backend.api_server
```

### Database Issues

```bash
# Check database integrity
sqlite3 data/sanchay_local.db "PRAGMA integrity_check;"

# Verify schema
sqlite3 data/sanchay_local.db ".schema"
```

### Performance Issues

```bash
# Check system resources
top
df -h
du -sh *

# Check database query performance
sqlite3 data/sanchay_local.db ".eqp on"
```

---

## 📞 Support

For deployment issues:
1. Check logs: `journalctl -u sanchay-api`
2. Test API: `curl http://localhost:8001/health`
3. Run tests: `pytest -vv`
4. Check configuration: `echo $API_HOST $API_PORT`

---

**Last Updated**: 2024
**Version**: 2.0.0
