# Production Deployment Guide

This guide covers deploying the nDART application in production using Gunicorn + Gevent.

## 🚀 **Quick Start**

### 1. **Deploy with Production Docker Compose**
```bash
# Copy and configure environment
cp env.production .env

# Edit the environment file
nano .env

# Deploy the application
docker-compose -f docker-compose.production.yml up -d
```

### 2. **Check Application Status**
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f ndart

# Test health endpoint
curl http://localhost:9030/health
```

## 🔧 **Configuration**

### **Environment Variables**
Edit `env.production` to configure your production environment:

```bash
# Security - CHANGE THESE!
SECRET_KEY=your-super-secret-production-key
NDART_DEBUG=False

# Database (choose one)
DATABASE_URL=sqlite:////app/db/app.db
# DATABASE_URL=postgresql://user:pass@host:port/db
# DATABASE_URL=mysql://user:pass@host:port/db
```

### **Gunicorn Configuration**
The production setup uses these Gunicorn settings:

- **Worker Class**: `gevent` (better WebSocket performance)
- **Workers**: `1` (required for SocketIO)
- **Worker Connections**: `1000` (concurrent connections)
- **Timeout**: `120` seconds
- **Keep-Alive**: `5` seconds
- **Max Requests**: `1000` (auto-restart workers)
- **Preload**: `True` (faster startup)

## 📊 **Performance Features**

### **Resource Limits**
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### **Health Checks**
- **Endpoint**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## 🔒 **Security Considerations**

### **1. Change Default Secrets**
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Update env.production
SECRET_KEY=your-generated-secret-key
```

### **2. Database Security**
- Use strong database passwords
- Enable SSL for external databases
- Regular backups

### **3. Network Security**
- Use reverse proxy (Nginx) for SSL termination
- Configure firewall rules
- Use Docker networks for isolation

## 🌐 **Reverse Proxy Setup (Recommended)**

### **Nginx Configuration**
```nginx
# /etc/nginx/sites-available/ndart
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:9030;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /socket.io/ {
        proxy_pass http://localhost:9030;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **SSL with Let's Encrypt**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 📈 **Scaling Options**

### **1. Horizontal Scaling**
```bash
# Run multiple instances
docker-compose -f docker-compose.production.yml up -d --scale ndart=3
```

### **2. Load Balancer Configuration**
```nginx
upstream ndart_backend {
    server localhost:9030;
    server localhost:9031;
    server localhost:9032;
}

server {
    listen 80;
    location / {
        proxy_pass http://ndart_backend;
        # ... proxy settings
    }
}
```

## 🔍 **Monitoring & Logging**

### **Application Logs**
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f ndart

# Log files are stored in ./logs/ directory
tail -f logs/app.log
```

### **Health Monitoring**
```bash
# Check application health
curl http://localhost:9030/health | jq

# Monitor resource usage
docker stats ndart-production
```

### **Database Monitoring**
```bash
# Check database status
docker-compose -f docker-compose.production.yml exec ndart python -c "
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM user'))
    print(f'Users in database: {result.scalar()}')
"
```

## 🛠 **Maintenance Commands**

### **Application Management**
```bash
# Restart application
docker-compose -f docker-compose.production.yml restart ndart

# Update application
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# View container status
docker-compose -f docker-compose.production.yml ps
```

### **Database Management**
```bash
# Run database migrations
docker-compose -f docker-compose.production.yml exec ndart flask db upgrade

# Initialize database (if needed)
docker-compose -f docker-compose.production.yml exec ndart python init_db.py

# Backup database
cp ./db/app.db ./backups/app-$(date +%Y%m%d-%H%M%S).db
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Port Already in Use**
```bash
# Check what's using port 9030
sudo netstat -tlnp | grep 9030

# Kill process if needed
sudo kill -9 <PID>
```

#### **2. Database Connection Issues**
```bash
# Check database file permissions
ls -la ./db/

# Fix permissions if needed
sudo chown -R $USER:$USER ./db/
```

#### **3. Memory Issues**
```bash
# Check memory usage
docker stats ndart-production

# Adjust resource limits in docker-compose.production.yml
```

### **Debug Mode**
```bash
# Run in debug mode (development only)
docker-compose -f docker-compose.production.yml run --rm ndart python app.py
```

## 📋 **Production Checklist**

- [ ] **Security**
  - [ ] Changed default SECRET_KEY
  - [ ] Set NDART_DEBUG=False
  - [ ] Configured secure database credentials
  - [ ] Set up SSL/TLS certificates

- [ ] **Database**
  - [ ] Database initialized and migrated
  - [ ] Backup strategy in place
  - [ ] Connection pooling configured

- [ ] **Monitoring**
  - [ ] Health checks working
  - [ ] Logging configured
  - [ ] Resource monitoring set up

- [ ] **Performance**
  - [ ] Gunicorn + Gevent configured
  - [ ] Resource limits set
  - [ ] Reverse proxy configured

- [ ] **Backup & Recovery**
  - [ ] Database backup automated
  - [ ] Application backup strategy
  - [ ] Disaster recovery plan

## 🎯 **Quick Commands**

```bash
# Deploy to production
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Restart
docker-compose -f docker-compose.production.yml restart

# Stop
docker-compose -f docker-compose.production.yml down
```

Your nDART application is now ready for production deployment! 🚀
