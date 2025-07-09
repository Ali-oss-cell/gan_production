# Gan7Club Production Deployment Guide

## 🚀 Complete Production Setup for Django Backend

### 1. Environment Configuration

#### Create Production Environment File
```bash
# On your server, create the production .env file
nano /home/root/talent-platform/.env
```

Copy the contents from `env.production.template` and update with your real values:

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=talent_platform.settings_production
SECRET_KEY=your-actual-secret-key-here
DEBUG=False

# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=api.gan7club.com,gan7club.com,www.gan7club.com

# Database Configuration (DigitalOcean Managed PostgreSQL)
DO_DB_NAME=your-actual-db-name
DO_DB_USER=your-actual-db-user
DO_DB_PASSWORD=your-actual-db-password
DO_DB_HOST=your-actual-db-host.digitaloceanspaces.com
DO_DB_PORT=25060

# Email Configuration (Hostinger SMTP)
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@gan7club.com
EMAIL_HOST_PASSWORD=your-actual-email-password
DEFAULT_FROM_EMAIL=noreply@gan7club.com
ADMIN_EMAIL=admin@gan7club.com

# DigitalOcean Spaces Configuration
USE_SPACES=True
SPACES_ACCESS_KEY=your-actual-spaces-access-key
SPACES_SECRET_KEY=your-actual-spaces-secret-key
SPACES_BUCKET_NAME=gan7club-media
SPACES_ENDPOINT_URL=https://fra1.digitaloceanspaces.com

# Stripe Configuration (Production Keys)
STRIPE_PUBLIC_KEY=pk_live_your-actual-stripe-public-key
STRIPE_SECRET_KEY=sk_live_your-actual-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-actual-webhook-secret

# Stripe Price IDs (Production)
STRIPE_PRICE_SILVER=price_your-actual-silver-price-id
STRIPE_PRICE_GOLD=price_your-actual-gold-price-id
STRIPE_PRICE_PLATINUM=price_your-actual-platinum-price-id
STRIPE_PRICE_BACKGROUND_JOBS=price_your-actual-background-jobs-price-id

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# File Paths
STATIC_ROOT=/home/root/talent-platform/staticfiles
MEDIA_ROOT=/home/root/talent-platform/media
```

### 2. Install Required Dependencies

```bash
# Activate virtual environment
source /home/root/talent-platform/venv/bin/activate

# Install required packages for production
pip install django-storages boto3 psycopg2-binary

# Update requirements.txt
pip freeze > requirements.txt
```

### 3. Database Setup

```bash
# Apply migrations
python manage.py migrate

# Create superuser (if needed)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 4. Gunicorn Configuration

#### Update Gunicorn Service File
```bash
nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=Gunicorn daemon for Gan7Club Django application
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/home/root/talent-platform/talent_platform
Environment="PATH=/home/root/talent-platform/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=talent_platform.settings_production"
ExecStart=/home/root/talent-platform/venv/bin/gunicorn --workers 3 --bind unix:/home/root/talent-platform/talent_platform/gunicorn.sock talent_platform.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 5. Nginx Configuration

#### Update Nginx Config
```bash
nano /etc/nginx/sites-available/gan7club
```

```nginx
server {
    listen 80;
    server_name api.gan7club.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.gan7club.com;

    # SSL Configuration (replace with your actual SSL certificate paths)
    ssl_certificate /etc/letsencrypt/live/api.gan7club.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.gan7club.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Client Max Body Size for file uploads
    client_max_body_size 100M;

    # Static Files
    location /static/ {
        alias /home/root/talent-platform/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django Application
    location / {
        proxy_pass http://unix:/home/root/talent-platform/talent_platform/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health Check Endpoint
    location /health/ {
        proxy_pass http://unix:/home/root/talent-platform/talent_platform/gunicorn.sock;
        proxy_set_header Host $host;
        access_log off;
    }
}
```

### 6. SSL Certificate Setup

```bash
# Install Certbot
apt update
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d api.gan7club.com

# Test auto-renewal
certbot renew --dry-run
```

### 7. Service Management

```bash
# Reload systemd and restart services
systemctl daemon-reload
systemctl restart gunicorn
systemctl enable gunicorn

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx
systemctl enable nginx
```

### 8. Firewall Configuration

```bash
# Allow HTTP, HTTPS, and SSH
ufw allow 80
ufw allow 443
ufw allow 22

# Enable firewall
ufw enable
```

### 9. Monitoring and Logs

#### Check Service Status
```bash
# Check Gunicorn status
systemctl status gunicorn

# Check Nginx status
systemctl status nginx

# View Gunicorn logs
journalctl -u gunicorn -f

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# View Django logs
tail -f /home/root/talent-platform/logs/django.log
```

#### Test Endpoints
```bash
# Test health endpoint
curl -I https://api.gan7club.com/health/

# Test admin endpoint
curl -I https://api.gan7club.com/admin/login/

# Test API endpoint
curl -I https://api.gan7club.com/api/
```

### 10. Performance Optimization

#### Database Optimization
```bash
# Create database indexes
python manage.py makemigrations
python manage.py migrate

# Analyze database performance
python manage.py dbshell
```

#### Cache Setup
```bash
# Create cache table
python manage.py createcachetable
```

### 11. Security Checklist

- [ ] SECRET_KEY is properly set and secure
- [ ] DEBUG is set to False
- [ ] ALLOWED_HOSTS contains only production domains
- [ ] CORS settings only allow production domains
- [ ] SSL certificate is installed and working
- [ ] Database uses SSL connection
- [ ] Email configuration is working
- [ ] Stripe keys are production keys
- [ ] DigitalOcean Spaces is configured
- [ ] File upload limits are set
- [ ] Rate limiting is enabled
- [ ] Security headers are configured

### 12. Troubleshooting

#### Common Issues and Solutions

1. **502 Bad Gateway**
   ```bash
   # Check Gunicorn status
   systemctl status gunicorn
   
   # Check socket file
   ls -la /home/root/talent-platform/talent_platform/gunicorn.sock
   
   # Restart Gunicorn
   systemctl restart gunicorn
   ```

2. **CORS Errors**
   - Verify CORS_ALLOWED_ORIGINS in settings_production.py
   - Check frontend domain is included
   - Restart Gunicorn after changes

3. **Database Connection Issues**
   ```bash
   # Test database connection
   python manage.py dbshell
   
   # Check environment variables
   echo $DO_DB_HOST
   ```

4. **Static Files Not Loading**
   ```bash
   # Recollect static files
   python manage.py collectstatic --noinput
   
   # Check permissions
   chmod -R 755 /home/root/talent-platform/staticfiles
   ```

### 13. Backup Strategy

```bash
# Database backup
pg_dump -h $DO_DB_HOST -U $DO_DB_USER -d $DO_DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Media files backup (if not using Spaces)
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz /home/root/talent-platform/media/
```

### 14. Maintenance Commands

```bash
# Update code
cd /home/root/talent-platform
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
systemctl restart gunicorn
systemctl reload nginx
```

---

## 🎯 Quick Deployment Checklist

1. ✅ Environment file configured
2. ✅ Dependencies installed
3. ✅ Database migrated
4. ✅ Static files collected
5. ✅ Gunicorn configured and running
6. ✅ Nginx configured and running
7. ✅ SSL certificate installed
8. ✅ Firewall configured
9. ✅ Services tested
10. ✅ Monitoring set up

Your Django backend is now production-ready! 🚀 