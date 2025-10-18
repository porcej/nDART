# WSGI Server Setup for Flask-SocketIO

This guide explains the WSGI server configuration for your nDART application with Flask-SocketIO support.

## 🔧 **Why WSGI Server for SocketIO?**

Your nDART application uses Flask-SocketIO, which requires:
- **WebSocket support** - Real-time bidirectional communication
- **Event-driven architecture** - Non-blocking I/O for SocketIO
- **Production-ready server** - Better performance than Flask dev server

## 🚀 **Current Setup: Gunicorn + Eventlet**

### Configuration Files:
- **`wsgi.py`** - WSGI application entry point
- **`gunicorn.conf.py`** - Gunicorn configuration
- **`Dockerfile`** - Updated to use Gunicorn

### Key Features:
- **Eventlet worker class** - Supports WebSockets and SocketIO
- **Single worker** - Required for SocketIO (eventlet limitation)
- **Optimized timeouts** - 120s for WebSocket connections
- **Memory management** - Worker recycling after 1000 requests

## 🔧 **WSGI Server Options**

### Option 1: Gunicorn + Eventlet (Current)
```bash
# Production deployment
gunicorn -c gunicorn.conf.py wsgi:application

# Manual configuration
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:9091 wsgi:application
```

### Option 2: Gunicorn + Gevent
```bash
# Alternative worker class
gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:9091 wsgi:application
```

### Option 3: UWSGI + Eventlet
```bash
# UWSGI configuration
uwsgi --http :9091 --wsgi-file wsgi.py --callable application --processes 1 --threads 2
```

## 🔧 **Configuration Details**

### Gunicorn Configuration (`gunicorn.conf.py`)

```python
# Worker configuration
workers = 1                    # Single worker for SocketIO
worker_class = "eventlet"      # Event-driven worker
worker_connections = 1000      # Max concurrent connections

# Timeouts
timeout = 120                  # 2 minutes for WebSocket connections
keepalive = 2                  # Keep connections alive

# Memory management
max_requests = 1000            # Restart worker after 1000 requests
max_requests_jitter = 100      # Random jitter to prevent thundering herd

# Performance
preload_app = True             # Preload application for better performance
```

### WSGI Entry Point (`wsgi.py`)

```python
from app import create_app, init_app
from extensions import socketio

# Create Flask app
app = create_app()
init_app(app)

# Export SocketIO app for WSGI
application = socketio
```

## 🔧 **Docker Integration**

### Updated Dockerfile
```dockerfile
# Install Gunicorn and eventlet
RUN pip install gunicorn eventlet

# Use Gunicorn instead of direct Python
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:application"]
```

### Docker Compose
```yaml
services:
  ndart:
    build: .
    ports:
      - "9091:9091"
    environment:
      - FLASK_ENV=production
    # Gunicorn handles the WSGI server
```

## 🔧 **Performance Optimization**

### 1. Worker Configuration
```python
# Single worker for SocketIO (eventlet limitation)
workers = 1
worker_class = "eventlet"
worker_connections = 1000
```

### 2. Connection Pooling
```python
# Keep connections alive
keepalive = 2
timeout = 120
```

### 3. Memory Management
```python
# Prevent memory leaks
max_requests = 1000
max_requests_jitter = 100
```

### 4. Preload Application
```python
# Better performance
preload_app = True
```

## 🔧 **Monitoring and Logging**

### Application Logs
```bash
# View Gunicorn logs
docker-compose logs -f ndart

# View specific worker logs
docker-compose exec ndart tail -f /app/logs/gunicorn.log
```

### Health Monitoring
```bash
# Check worker status
docker-compose exec ndart ps aux | grep gunicorn

# Check SocketIO connections
curl http://localhost:9091/health
```

### Performance Metrics
```bash
# Monitor worker processes
docker-compose exec ndart ps -ef | grep gunicorn

# Check memory usage
docker-compose exec ndart free -h
```

## 🔧 **Scaling Considerations**

### Single Worker Limitation
- **Eventlet limitation**: Only 1 worker process
- **Solution**: Use multiple containers behind load balancer
- **Alternative**: Use gevent worker class

### Load Balancing
```yaml
# Multiple containers
services:
  ndart-1:
    build: .
    ports: ["9091:9091"]
  ndart-2:
    build: .
    ports: ["9092:9091"]
  nginx:
    # Load balance between containers
    upstream ndart_backend {
        server ndart-1:9091;
        server ndart-2:9091;
    }
```

## 🔧 **Troubleshooting**

### Common Issues

#### 1. WebSocket Connection Failed
```bash
# Check if eventlet is working
docker-compose exec ndart python -c "
import eventlet
print('Eventlet version:', eventlet.__version__)
"
```

#### 2. Worker Timeout
```bash
# Increase timeout in gunicorn.conf.py
timeout = 300  # 5 minutes
```

#### 3. Memory Issues
```bash
# Monitor memory usage
docker-compose exec ndart ps aux | grep gunicorn
```

#### 4. SocketIO Not Working
```bash
# Check SocketIO configuration
docker-compose exec ndart python -c "
from extensions import socketio
print('SocketIO configured:', socketio is not None)
"
```

### Debug Commands
```bash
# Test WSGI application
docker-compose exec ndart python wsgi.py

# Test Gunicorn configuration
docker-compose exec ndart gunicorn --check-config -c gunicorn.conf.py wsgi:application

# Test SocketIO connection
curl -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:9091/socket.io/
```

## 🔧 **Production Deployment**

### Environment Variables
```bash
# Production settings
export FLASK_ENV=production
export WORKERS=1
export WORKER_CLASS=eventlet
export TIMEOUT=120
```

### Docker Compose Production
```yaml
services:
  ndart:
    build: .
    environment:
      - FLASK_ENV=production
      - WORKERS=1
      - WORKER_CLASS=eventlet
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9091/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 🔧 **Alternative Configurations**

### Gevent Worker (Alternative)
```python
# gunicorn.conf.py
worker_class = "gevent"
workers = 1
worker_connections = 1000
```

### Multiple Workers (Not Recommended for SocketIO)
```python
# Only if you don't need SocketIO
worker_class = "sync"
workers = 4
```

## 🔧 **Quick Commands**

```bash
# Development (Flask dev server)
python app.py

# Production (Gunicorn + eventlet)
gunicorn -c gunicorn.conf.py wsgi:application

# Docker production
docker-compose up -d

# Check status
curl http://localhost:9091/health

# View logs
docker-compose logs -f ndart
```

## 🔧 **Best Practices**

1. **Use eventlet worker** for SocketIO applications
2. **Single worker** for SocketIO (eventlet limitation)
3. **Monitor memory usage** and restart workers
4. **Use load balancer** for scaling
5. **Configure proper timeouts** for WebSocket connections
6. **Enable logging** for debugging
7. **Use health checks** for monitoring
