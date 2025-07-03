# 🚀 DigitalOcean Deployment Checklist

## ✅ Pre-Deployment (COMPLETED)
- [x] Repository cleaned up and pushed to GitHub
- [x] Environment variables configured
- [x] DigitalOcean Spaces bucket created (ganspace)
- [x] DigitalOcean managed PostgreSQL database created (db-postgresql-fra1-05452)
- [x] Stripe account configured
- [x] Hostinger SMTP configured
- [x] Production settings updated

## 🔧 Server Setup (DigitalOcean Droplet)

### 1. Connect to Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### 2. Update System
```bash
apt update && apt upgrade -y
```

### 3. Install Required Software
```bash
# Install Python 3.11
apt install python3.11 python3.11-venv python3.11-dev -y

# Install PostgreSQL client
apt install postgresql-client -y

# Install Nginx
apt install nginx -y

# Install Git
apt install git -y

# Install build tools
apt install build-essential -y
```

### 4. Create Application Directory
```bash
mkdir -p /home/root/talent-platform
cd /home/root/talent-platform
```

### 5. Clone Repository
```bash
git clone https://github.com/Ali-oss-cell/gan_production.git .
```

### 6. Set Up Python Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Create Environment File
```bash
nano .env
```

**Add your environment variables:**
```env
# Django Backend (API)
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=api.gan7club.com,YOUR_DROPLET_IP

# DigitalOcean Database
DO_DB_HOST=db-postgresql-fra1-05452-do-user-12345678-0.b.db.ondigitalocean.com
DO_DB_NAME=defaultdb
DO_DB_USER=doadmin
DO_DB_PASSWORD=your_database_password
DO_DB_PORT=25060

# DigitalOcean Spaces
USE_SPACES=True
SPACES_ACCESS_KEY=your_spaces_access_key
SPACES_SECRET_KEY=your_spaces_secret_key
SPACES_BUCKET_NAME=ganspace
SPACES_ENDPOINT_URL=https://fra1.digitaloceanspaces.com

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_lzIMy9lvp1zgrM4qGr8Yy2mJ5vGHDbLC

# Email (Hostinger SMTP)
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Frontend URL (for email verification links - your React app domain)
FRONTEND_URL=https://gan7club.com
```

### 8. Run Django Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate --settings=talent_platform.settings_production

# Create superuser
python manage.py createsuperuser --settings=talent_platform.settings_production

# Collect static files
python manage.py collectstatic --settings=talent_platform.settings_production --noinput

# Create logs directory
mkdir -p logs
```

### 9. Test the Application
```bash
python manage.py runserver 0.0.0.0:8000 --settings=talent_platform.settings_production
```

## 🌐 Nginx Configuration

### 10. Create Nginx Configuration
```bash
nano /etc/nginx/sites-available/talent-platform
```

**Add this configuration for API subdomain:**
```nginx
server {
    listen 80;
    server_name api.gan7club.com YOUR_DROPLET_IP;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/root/talent-platform;
    }

    location /media/ {
        root /home/root/talent-platform;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/root/talent-platform/talent-platform.sock;
    }
}
```

### 11. Enable Site
```bash
ln -s /etc/nginx/sites-available/talent-platform /etc/nginx/sites-enabled
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

## 🔄 Gunicorn Configuration

### 12. Create Gunicorn Service
```bash
nano /etc/systemd/system/talent-platform.service
```

**Add this configuration:**
```ini
[Unit]
Description=Talent Platform Gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/home/root/talent-platform
Environment="PATH=/home/root/talent-platform/venv/bin"
ExecStart=/home/root/talent-platform/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/root/talent-platform/talent-platform.sock talent_platform.wsgi:application --env DJANGO_SETTINGS_MODULE=talent_platform.settings_production

[Install]
WantedBy=multi-user.target
```

### 13. Start Gunicorn Service
```bash
systemctl start talent-platform
systemctl enable talent-platform
systemctl status talent-platform
```

## 🔒 SSL Certificate (Let's Encrypt)

### 14. Install Certbot
```bash
apt install certbot python3-certbot-nginx -y
```

### 15. Get SSL Certificate for API
```bash
certbot --nginx -d api.gan7club.com
```

## 🧪 Final Testing

### 16. Test Your Django API
- Test API endpoints: `https://api.gan7club.com/api/`
- Test user registration
- Test file uploads
- Test payment integration
- Check logs: `tail -f /home/root/talent-platform/logs/django.log`

### 17. Deploy React Frontend to DigitalOcean App Platform
- Deploy your React app to DigitalOcean App Platform
- Configure custom domain: `gan7club.com`
- Set API base URL to: `https://api.gan7club.com`
- Test email verification links work correctly

### 18. DigitalOcean App Platform Setup
1. **Create App in DigitalOcean Console**
   - Go to DigitalOcean Console → Apps → Create App
   - Connect your GitHub repository (React app)
   - Choose Node.js environment

2. **Configure Build Settings**
   ```yaml
   # app.yaml or build command
   build_command: npm run build
   run_command: npm start
   ```

3. **Environment Variables for React App**
   ```env
   REACT_APP_API_BASE_URL=https://api.gan7club.com
   REACT_APP_FRONTEND_URL=https://gan7club.com
   ```

4. **Custom Domain Setup**
   - In App Platform settings, add custom domain: `gan7club.com`
   - Update DNS records in Hostinger to point to App Platform

## 📋 Environment Variables Reference

Make sure you have these values ready:
- **Database**: From DigitalOcean managed database
- **Spaces**: From DigitalOcean Spaces (ganspace bucket)
- **Stripe**: From your Stripe dashboard
- **Email**: From Hostinger SMTP settings
- **Domain**: Your registered domain name
- **Frontend URL**: Your React app domain for email verification links

## 🌐 Domain Setup for React + Django

### DNS Configuration (in Hostinger for gan7club.com):
```
Type    Name    Value
A       @       DIGITALOCEAN_APP_PLATFORM_IP (for gan7club.com)
CNAME   api     gan7club.com (points to YOUR_DROPLET_IP)
```

**Note:** You'll get the App Platform IP from DigitalOcean when you deploy your React app.

### React App Configuration:
```javascript
// In your React app, set API base URL
const API_BASE_URL = 'https://api.gan7club.com';

// Example API calls
fetch(`${API_BASE_URL}/api/users/login/`, {
  method: 'POST',
  // ... rest of your API calls
});
```

## 📧 Email Verification System

Your platform includes a comprehensive email verification system:
- ✅ Users receive verification emails upon registration
- ✅ Verification links expire after 24 hours
- ✅ Automatic re-sending of expired verification links
- ✅ Email verification status tracked in user accounts
- ✅ Verification URLs use environment variables for production

## 💳 Stripe Webhook Configuration

Your payment system includes webhook handling:
- ✅ Webhook endpoint: `https://api.gan7club.com/api/payments/webhook/`
- ✅ Webhook secret: `whsec_lzIMy9lvp1zgrM4qGr8Yy2mJ5vGHDbLC`
- ✅ Signature verification enabled
- ✅ Handles payment events, subscriptions, and customer updates

## 🚨 Important Notes

1. **Security**: Change default SSH port and set up firewall
2. **Backups**: Set up regular database backups
3. **Monitoring**: Consider setting up monitoring tools
4. **Updates**: Keep system and packages updated
5. **Logs**: Monitor application logs regularly

## 🆘 Troubleshooting

- **Check Gunicorn logs**: `journalctl -u talent-platform`
- **Check Nginx logs**: `tail -f /var/log/nginx/error.log`
- **Check Django logs**: `tail -f /home/root/talent-platform/logs/django.log`
- **Restart services**: `systemctl restart talent-platform nginx`

---

**You're ready to deploy! 🎉** 