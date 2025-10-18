# Configuration Guide

This document explains how to configure the nDART application for different environments.

## 🔧 **Environment Configuration**

The application supports multiple configuration classes:

- **Development**: Local development with debug enabled
- **Production**: Production deployment with security optimizations  
- **Testing**: Unit testing configuration
- **Docker**: Docker-specific configuration

## 📋 **Environment Variables**

### **Required Variables**

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` | `your-super-secret-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///db/app.db` | `postgresql://user:pass@host:port/db` |

### **Application Settings**

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `FLASK_ENV` | Environment mode | `development` | `production` |
| `MED_TRACKER_DEBUG` | Enable debug mode | `False` | `True` |
| `MED_TRACKER_HOST` | Host to bind application | `0.0.0.0` | `127.0.0.1` |
| `FLASK_PORT` | Port to run application | `9091` | `5000` |

### **Logging Configuration**

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOGGING_PATH` | Directory for log files | `logs` | `/var/log/ndart` |
| `LOGGING_LEVEL` | Logging level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL) | `20` | `30` |

### **SocketIO Configuration**

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ASYNC_MODE` | SocketIO async mode | `None` (auto-detect) | `gevent` |

### **File Upload Configuration**

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `UPLOAD_FOLDER` | Directory for file uploads | `uploads` | `/var/uploads` |
| `MAX_CONTENT_LENGTH` | Maximum file upload size (bytes) | `16777216` (16MB) | `33554432` (32MB) |

### **Security Settings**

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SESSION_COOKIE_SECURE` | Secure session cookies | `False` | `True` |
| `WTF_CSRF_ENABLED` | Enable CSRF protection | `True` | `False` |
| `RATELIMIT_ENABLED` | Enable rate limiting | `True` | `False` |

## 🚀 **Environment Setup**

### **Development Environment**

```bash
# .env file for development
FLASK_ENV=development
MED_TRACKER_DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///db/dev.db
LOGGING_LEVEL=10
```

### **Production Environment**

```bash
# .env file for production
FLASK_ENV=production
MED_TRACKER_DEBUG=False
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://user:pass@host:port/database
LOGGING_LEVEL=30
SESSION_COOKIE_SECURE=True
```

### **Docker Environment**

```bash
# Environment variables for Docker
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:////app/db/app.db
LOGGING_PATH=/app/logs
UPLOAD_FOLDER=/app/uploads
```

## 🔒 **Security Configuration**

### **Production Security Checklist**

- [ ] **SECRET_KEY**: Use a strong, random secret key
- [ ] **SESSION_COOKIE_SECURE**: Set to `True` for HTTPS
- [ ] **WTF_CSRF_ENABLED**: Keep enabled for production
- [ ] **RATELIMIT_ENABLED**: Enable rate limiting
- [ ] **Database**: Use secure database credentials
- [ ] **Logging**: Set appropriate log levels

### **Secret Key Generation**

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Or using OpenSSL
openssl rand -hex 32
```

## 🗄️ **Database Configuration**

### **SQLite (Development)**

```bash
DATABASE_URL=sqlite:///db/app.db
```

### **PostgreSQL (Production)**

```bash
DATABASE_URL=postgresql://username:password@host:port/database_name
```

### **MySQL (Production)**

```bash
DATABASE_URL=mysql://username:password@host:port/database_name
```

## 📊 **Logging Configuration**

### **Log Levels**

| Level | Value | Description |
|-------|-------|-------------|
| CRITICAL | 50 | Critical errors only |
| ERROR | 40 | Error messages and above |
| WARNING | 30 | Warning messages and above |
| INFO | 20 | Informational messages and above |
| DEBUG | 10 | Debug messages and above |
| VERBOSE | 1 | All messages |

### **Log File Locations**

- **Development**: `./logs/app.log`
- **Production**: `/var/log/ndart/app.log`
- **Docker**: `/app/logs/app.log`

## 🔧 **Configuration Classes**

### **DevelopmentConfig**

- Debug mode enabled
- Verbose logging
- CSRF disabled for development
- SQLite database

### **ProductionConfig**

- Debug mode disabled
- Security optimizations
- CSRF protection enabled
- Rate limiting enabled
- Database connection pooling

### **TestingConfig**

- Testing mode enabled
- In-memory database
- CSRF disabled
- Rate limiting disabled

### **DockerConfig**

- Docker-optimized paths
- Production security settings
- Container-specific configurations

## 🚀 **Quick Start**

### **1. Copy Environment Template**

```bash
# For development
cp env.example .env

# For production
cp env.production .env
```

### **2. Configure Environment Variables**

```bash
# Edit the .env file
nano .env
```

### **3. Set Required Variables**

```bash
# Generate secret key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Set environment
export SECRET_KEY
export FLASK_ENV=production
```

### **4. Start Application**

```bash
# Development
python app.py

# Production with Docker
docker-compose -f docker-compose.production.yml up -d
```

## 🔍 **Configuration Validation**

The application validates configuration on startup:

- **SECRET_KEY**: Must be set in production
- **Database**: Connection must be valid
- **Directories**: Required directories are created automatically
- **Security**: Production security settings are enforced

## 📝 **Configuration Examples**

### **Complete Development Setup**

```bash
# .env file
FLASK_ENV=development
MED_TRACKER_DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///db/dev.db
LOGGING_LEVEL=10
ASYNC_MODE=threading
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

### **Complete Production Setup**

```bash
# .env file
FLASK_ENV=production
MED_TRACKER_DEBUG=False
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://user:pass@host:port/database
LOGGING_LEVEL=30
SESSION_COOKIE_SECURE=True
WTF_CSRF_ENABLED=True
RATELIMIT_ENABLED=True
ASYNC_MODE=gevent
UPLOAD_FOLDER=/var/uploads
MAX_CONTENT_LENGTH=16777216
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **SECRET_KEY not set**: Application will fail to start in production
2. **Database connection failed**: Check DATABASE_URL format
3. **Permission denied**: Check directory permissions for logs/uploads
4. **CSRF errors**: Ensure WTF_CSRF_ENABLED is set correctly

### **Debug Configuration**

```bash
# Enable debug mode
export MED_TRACKER_DEBUG=True
export LOGGING_LEVEL=10

# Check configuration
python -c "from config import get_config; print(get_config().__dict__)"
```

This configuration system provides a robust, secure, and flexible way to manage your nDART application across different environments! 🚀
