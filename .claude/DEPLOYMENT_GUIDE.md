# Muni-Info Deployment Guide

## Overview
This guide covers deployment options for the Muni-Info municipal service platform, from development setup to production deployment.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux (Ubuntu 18.04+), Windows 10+, macOS 10.15+
- **Memory**: Minimum 2GB RAM, 4GB+ recommended
- **Storage**: Minimum 5GB free space
- **Network**: Internet connection for external API calls

### External Services
- **Twilio Account**: For WhatsApp Business API
  - Account SID and Auth Token
  - WhatsApp Business number (sandbox for development)
- **Google Maps API**: (Optional) For enhanced geocoding
  - API key with Geocoding and Places API enabled
- **Domain & SSL**: For production deployment

## Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd muni-info
```

### 2. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

Required environment variables:
```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key  # Optional
```

### 5. Initialize Data Directories
```bash
mkdir -p data/media
```

### 6. Run Development Server
```bash
python main.py
```

The application will be available at:
- **Public Portal**: http://localhost:5000/portal/
- **Admin Dashboard**: http://localhost:5000/admin/ (admin/admin123)
- **API Documentation**: http://localhost:5000/api/v1/docs

### 7. Configure Twilio Webhook
In your Twilio Console:
1. Go to WhatsApp sandbox settings
2. Set webhook URL to: `http://your-domain.com/whatsapp`
3. Set HTTP method to POST

For local development, use ngrok:
```bash
# Install ngrok and expose local server
ngrok http 5000

# Use the ngrok URL in Twilio webhook settings
# e.g., https://abc123.ngrok.io/whatsapp
```

## Production Deployment

### Option 1: Traditional Server Deployment

#### 1. Server Setup (Ubuntu 20.04)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Create application user
sudo adduser --system --group muniinfo
```

#### 2. Application Setup
```bash
# Switch to application user
sudo su - muniinfo

# Clone repository
git clone <repository-url> /home/muniinfo/muni-info
cd /home/muniinfo/muni-info

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with production values
```

#### 3. Production Environment Variables
```bash
# /home/muniinfo/muni-info/.env
TWILIO_ACCOUNT_SID=your_production_twilio_sid
TWILIO_AUTH_TOKEN=your_production_twilio_token
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Database settings (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost/muniinfo
```

#### 4. Gunicorn Configuration
```bash
# Create gunicorn configuration
sudo nano /home/muniinfo/muni-info/gunicorn.conf.py
```

```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "/var/log/muniinfo/access.log"
errorlog = "/var/log/muniinfo/error.log"
loglevel = "info"
```

#### 5. Supervisor Configuration
```bash
# Create supervisor config
sudo nano /etc/supervisor/conf.d/muniinfo.conf
```

```ini
[program:muniinfo]
command=/home/muniinfo/muni-info/venv/bin/gunicorn --config gunicorn.conf.py main:app
directory=/home/muniinfo/muni-info
user=muniinfo
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/muniinfo/app.log
environment=PATH="/home/muniinfo/muni-info/venv/bin"
```

```bash
# Create log directory
sudo mkdir -p /var/log/muniinfo
sudo chown muniinfo:muniinfo /var/log/muniinfo

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start muniinfo
```

#### 6. Nginx Configuration
```bash
# Create nginx site configuration
sudo nano /etc/nginx/sites-available/muniinfo
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Static files
    location /static {
        alias /home/muniinfo/muni-info/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media {
        alias /home/muniinfo/muni-info/data/media;
        expires 30d;
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/api/v1/health;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/muniinfo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data/media

# Create non-root user
RUN useradd --create-home --shell /bin/bash muniinfo
RUN chown -R muniinfo:muniinfo /app
USER muniinfo

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "main:app"]
```

#### 2. Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - SECRET_KEY=${SECRET_KEY}
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

#### 3. Build and Run
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale application
docker-compose up -d --scale app=3
```

### Option 3: Cloud Deployment (AWS)

#### 1. EC2 Instance Setup
```bash
# Launch EC2 instance (t3.small or larger)
# Security Groups: HTTP (80), HTTPS (443), SSH (22)

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Application Load Balancer
```bash
# Create ALB with SSL certificate
# Target Group: Port 8000, Health Check: /api/v1/health
# Route traffic to EC2 instances
```

#### 3. RDS Database (Optional)
```python
# Update configuration for PostgreSQL
pip install psycopg2-binary

# Database migration script
python migrate_to_postgres.py
```

### Option 4: Heroku Deployment

#### 1. Heroku Setup
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create application
heroku create muni-info-production

# Set environment variables
heroku config:set TWILIO_ACCOUNT_SID=your_sid
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set SECRET_KEY=your_secret_key
heroku config:set FLASK_ENV=production
```

#### 2. Create Heroku Files
```python
# Procfile
web: gunicorn main:app --workers 4 --bind 0.0.0.0:$PORT
```

```txt
# runtime.txt
python-3.9.10
```

#### 3. Deploy
```bash
# Deploy to Heroku
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Set up Twilio webhook
# URL: https://your-app.herokuapp.com/whatsapp
```

## Database Migration (Optional)

### PostgreSQL Setup
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql
CREATE DATABASE muniinfo;
CREATE USER muniinfo WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE muniinfo TO muniinfo;
```

### Migration Script
```python
# migrate_to_postgres.py
import json
import psycopg2
from datetime import datetime

# Migration logic to convert JSON files to PostgreSQL tables
# This would be a custom script based on your data structure
```

## Monitoring & Logging

### 1. Application Monitoring
```python
# Add to requirements.txt
prometheus-flask-exporter==0.18.2

# In main.py
from prometheus_flask_exporter import PrometheusMetrics

app = create_app()
metrics = PrometheusMetrics(app)
```

### 2. Log Configuration
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/muniinfo.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 3. System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Set up log rotation
sudo nano /etc/logrotate.d/muniinfo
```

```
/var/log/muniinfo/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 muniinfo muniinfo
}
```

## Backup & Recovery

### 1. Data Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/muniinfo/backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup data files
tar -czf $BACKUP_DIR/muniinfo_data_$DATE.tar.gz /home/muniinfo/muni-info/data/

# Backup logs
tar -czf $BACKUP_DIR/muniinfo_logs_$DATE.tar.gz /var/log/muniinfo/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. Automated Backup
```bash
# Add to crontab
crontab -e

# Backup daily at 2 AM
0 2 * * * /home/muniinfo/backup.sh
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Ubuntu UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Application Security
```python
# Security headers middleware
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 3. Environment Security
```bash
# Secure environment file
chmod 600 .env
chown muniinfo:muniinfo .env

# Secure data directory
chmod 755 data/
chmod 644 data/*.json
```

## Performance Optimization

### 1. Application Optimization
```python
# Add Redis caching
pip install redis flask-caching

# In config.py
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379"
```

### 2. Database Optimization
```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
CREATE INDEX idx_complaints_municipality ON complaints(municipality);
```

### 3. CDN Setup
```bash
# Configure CloudFlare or AWS CloudFront for static assets
# Update nginx configuration to set proper cache headers
```

## Maintenance Tasks

### 1. Regular Updates
```bash
#!/bin/bash
# update.sh
cd /home/muniinfo/muni-info
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart muniinfo
```

### 2. Health Checks
```bash
# health_check.sh
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)
if [ $response -ne 200 ]; then
    echo "Application unhealthy, restarting..."
    sudo supervisorctl restart muniinfo
fi
```

### 3. Log Cleanup
```bash
# Clean old media files
find /home/muniinfo/muni-info/data/media -type f -mtime +90 -delete
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check logs
sudo supervisorctl status muniinfo
sudo tail -f /var/log/muniinfo/error.log

# Check environment variables
sudo -u muniinfo env
```

#### 2. WhatsApp Webhook Issues
```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "Body=test&From=%2B27123456789"
```

#### 3. Database Connection Issues
```bash
# Check database connectivity
python -c "import psycopg2; conn = psycopg2.connect('your_connection_string'); print('Connected')"
```

### Performance Issues
```bash
# Monitor resource usage
htop
iotop
df -h

# Check application metrics
curl http://localhost:8000/metrics
```

## Scaling Considerations

### Horizontal Scaling
- Load balancer configuration
- Multiple application instances
- Shared data storage (NFS, S3)
- Redis cluster for caching

### Vertical Scaling
- Increase server resources
- Optimize application settings
- Database performance tuning
- CDN implementation

This deployment guide covers most common deployment scenarios. Choose the option that best fits your infrastructure requirements and technical expertise.