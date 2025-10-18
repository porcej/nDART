# Middleware Setup for nDART

This guide explains how to add middleware layers to your nDART application for production deployment.

## 🔧 **Current Setup (No Middleware)**

Your current setup runs the Flask app directly:
- **Port**: 9091 (exposed directly)
- **No reverse proxy**
- **No SSL termination**
- **No load balancing**

## 🚀 **Production Middleware Options**

### Option 1: Nginx Reverse Proxy (Recommended)

#### Benefits:
- SSL termination
- Rate limiting
- Load balancing
- Static file serving
- Security headers
- WebSocket support

#### Setup:
```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d

# Or with monitoring
docker-compose -f docker-compose.production.yml --profile monitoring up -d
```

### Option 2: Traefik (Modern Alternative)

Create `docker-compose.traefik.yml`:
```yaml
services:
  traefik:
    image: traefik:v2.10
    container_name: ndart-traefik
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.letsencrypt.acme.tlschallenge=true
      - --certificatesresolvers.letsencrypt.acme.email=your-email@example.com
      - --certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json

  ndart:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ndart.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.ndart.entrypoints=websecure"
      - "traefik.http.routers.ndart.tls.certresolver=letsencrypt"
      - "traefik.http.services.ndart.loadbalancer.server.port=9091"
```

### Option 3: Apache HTTP Server

Create `apache.conf`:
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com
    
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    ProxyPreserveHost On
    ProxyPass / http://ndart-app:9091/
    ProxyPassReverse / http://ndart-app:9091/
    
    # WebSocket support
    ProxyPass /socket.io/ ws://ndart-app:9091/socket.io/
    ProxyPassReverse /socket.io/ ws://ndart-app:9091/socket.io/
</VirtualHost>
```

## 🔧 **Middleware Features**

### 1. SSL/TLS Termination
```nginx
# Nginx SSL configuration
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
ssl_protocols TLSv1.2 TLSv1.3;
```

### 2. Rate Limiting
```nginx
# API rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;

# Login rate limiting
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req zone=login burst=5 nodelay;
```

### 3. Load Balancing
```nginx
upstream ndart_backend {
    server ndart-app-1:9091;
    server ndart-app-2:9091;
    server ndart-app-3:9091;
}
```

### 4. Security Headers
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 5. WebSocket Support
```nginx
location /socket.io/ {
    proxy_pass http://ndart_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## 🔧 **Monitoring and Logging**

### 1. Application Logs
```bash
# View application logs
docker-compose logs -f ndart

# View nginx logs
docker-compose logs -f nginx
```

### 2. Health Monitoring
```bash
# Check application health
curl https://your-domain.com/health

# Check nginx health
curl http://localhost/health
```

### 3. Prometheus Metrics
```yaml
# Add to docker-compose.production.yml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
```

## 🔧 **Deployment Commands**

### Development (No Middleware)
```bash
docker-compose up -d
```

### Production (With Nginx)
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Production (With Monitoring)
```bash
docker-compose -f docker-compose.production.yml --profile monitoring up -d
```

### Production (With Traefik)
```bash
docker-compose -f docker-compose.traefik.yml up -d
```

## 🔧 **SSL Certificate Setup**

### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
```

### Self-Signed Certificates (Development)
```bash
# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
```

## 🔧 **Performance Optimization**

### 1. Nginx Caching
```nginx
# Cache static files
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 2. Gzip Compression
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript;
```

### 3. Connection Pooling
```nginx
upstream ndart_backend {
    server ndart-app:9091 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

## 🔧 **Security Considerations**

### 1. Firewall Rules
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 9091/tcp  # Block direct access to app
```

### 2. Rate Limiting
```nginx
# Prevent brute force attacks
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
```

### 3. DDoS Protection
```nginx
# Limit connections per IP
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
limit_conn conn_limit_per_ip 20;
```

## 🔧 **Troubleshooting**

### Check Middleware Status
```bash
# Check nginx status
docker-compose exec nginx nginx -t

# Check application status
docker-compose exec ndart curl localhost:9091/health

# Check SSL certificate
openssl x509 -in ssl/cert.pem -text -noout
```

### Common Issues
1. **SSL Certificate Errors**: Check certificate path and permissions
2. **WebSocket Issues**: Ensure proper proxy headers
3. **Rate Limiting**: Adjust limits in nginx.conf
4. **Load Balancing**: Check upstream server health

## 🔧 **Quick Start Commands**

```bash
# 1. Setup SSL certificates
mkdir -p ssl
# Add your certificates to ssl/ directory

# 2. Start with middleware
docker-compose -f docker-compose.production.yml up -d

# 3. Check status
curl https://your-domain.com/health

# 4. View logs
docker-compose -f docker-compose.production.yml logs -f
```
