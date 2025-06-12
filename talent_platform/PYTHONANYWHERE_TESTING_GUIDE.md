# 🚀 PythonAnywhere Testing Deployment Guide

## Quick Setup for Testing

### 1. **Generate Secret Key First!** 🔑
Run this locally to generate a new secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. **Create .env File**
Copy `env_template.txt` to `.env` and update:
```env
SECRET_KEY=your_generated_secret_key_from_step_1
ALLOWED_HOSTS=localhost,127.0.0.1,yourusername.pythonanywhere.com
```

### 3. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit - talent platform with shared media"
git branch -M main
git remote add origin https://github.com/yourusername/talent-platform.git
git push -u origin main
```

## PythonAnywhere Setup

### 1. **Clone Project**
In PythonAnywhere Bash console:
```bash
git clone https://github.com/yourusername/talent-platform.git
cd talent-platform
```

### 2. **Install Dependencies**
```bash
pip3.10 install --user -r requirements.txt
```

### 3. **Create .env File**
```bash
cp env_template.txt .env
nano .env  # Edit with your values
```

### 4. **Run Migrations**
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. **Collect Static Files**
```bash
python manage.py collectstatic --noinput
```

### 6. **Web App Configuration**

**Source code:** `/home/yourusername/talent-platform`
**Working directory:** `/home/yourusername/talent-platform`

**WSGI configuration:**
```python
import sys
import os

path = '/home/yourusername/talent-platform'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'talent_platform.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Static files:**
- URL: `/static/` → Directory: `/home/yourusername/talent-platform/static/`
- URL: `/media/` → Directory: `/home/yourusername/talent-platform/media/`

### 7. **Test Your Shared Media Feature!**

Visit your site:
- `https://yourusername.pythonanywhere.com/admin/` - Admin panel
- `https://yourusername.pythonanywhere.com/api/dashboard/shared-media/` - Public gallery
- Create dashboard user and test sharing!

## 🎯 **What Works in Testing:**
- ✅ Shared media functionality
- ✅ Public gallery (no auth needed)
- ✅ Dashboard admin features
- ✅ SQLite database (sufficient for testing)
- ✅ All your existing features

## 📝 **Next Steps After Testing:**
1. Test all functionality thoroughly
2. Set up Stripe test payments
3. Test media sharing workflow
4. When ready for production: upgrade to paid tier + PostgreSQL 