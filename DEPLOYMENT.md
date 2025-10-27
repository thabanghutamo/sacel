# SACEL Deployment Guide

## Cloud Deployment Fixes Applied

### 1. Updated Dependencies
- **Fixed Pillow version** from 10.1.0 to 10.4.0 (Python 3.13 compatible)
- **Updated Flask** to 3.0.0 for better stability
- **Upgraded core dependencies** for Python 3.13 compatibility
- **Removed problematic packages** like `python-magic` and replaced with `python-magic-bin`

### 2. Added Deployment Configuration

#### `runtime.txt`
Specifies Python 3.11.9 for more stable cloud deployment (3.13 is too new for most platforms)

#### `Procfile`
```
web: gunicorn --bind 0.0.0.0:$PORT main:app
worker: python -c "print('Worker process started')"
```

#### `requirements-production.txt`
Minimal production requirements without development tools for faster builds.

### 3. Environment Variables Needed

For cloud deployment, ensure these environment variables are set:

```bash
# Database (use cloud MySQL/PostgreSQL)
DATABASE_URL=mysql://user:password@host:port/database

# Redis (use cloud Redis)
REDIS_URL=redis://user:password@host:port

# Security
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production

# AI Integration (optional)
OPENAI_API_KEY=your-openai-api-key

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 4. Deployment Options

#### Option A: Use Production Requirements
Replace `requirements.txt` with `requirements-production.txt` in your deployment:
```bash
cp requirements-production.txt requirements.txt
```

#### Option B: Build with Python 3.11
Set Python version to 3.11.9 in your cloud platform settings.

#### Option C: Railway Specific
If using Railway, the deployment should now work with the updated requirements.

### 5. Post-Deployment Steps

1. **Run database migrations**:
   ```bash
   flask db upgrade
   ```

2. **Set up admin user** (create a script or use the seed.py)

3. **Test the application** endpoints

## Troubleshooting

If you still encounter issues:

1. **Use requirements-production.txt** instead of the full requirements.txt
2. **Set Python version to 3.11.9** instead of 3.13
3. **Remove Pillow completely** if image processing isn't critical
4. **Check platform-specific documentation** for your cloud provider

## Security Notes

- The GitHub security alert shows 26 vulnerabilities - these are mainly from development dependencies
- Using `requirements-production.txt` reduces the attack surface
- Ensure all environment variables are properly configured
- Use HTTPS in production (most cloud platforms handle this automatically)