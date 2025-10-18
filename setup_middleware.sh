#!/bin/bash
# Middleware Setup Script for nDART

set -e

echo "🚀 Setting up middleware for nDART application..."

# Create necessary directories
mkdir -p ssl static monitoring

# Check if SSL certificates exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo "⚠️  SSL certificates not found. Creating self-signed certificates for development..."
    
    # Generate self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=nDART/CN=localhost" \
        2>/dev/null
    
    echo "✅ Self-signed SSL certificates created"
else
    echo "✅ SSL certificates found"
fi

# Create Prometheus configuration
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ndart'
    static_configs:
      - targets: ['ndart-app:9091']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF

echo "✅ Prometheus configuration created"

# Create Traefik configuration
cat > traefik.yml << EOF
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false

certificatesResolvers:
  letsencrypt:
    acme:
      tlsChallenge: {}
      email: your-email@example.com
      storage: /letsencrypt/acme.json
EOF

echo "✅ Traefik configuration created"

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "✅ Permissions set for SSL certificates"

echo ""
echo "🎉 Middleware setup complete!"
echo ""
echo "Available deployment options:"
echo "1. Development (no middleware): docker-compose up -d"
echo "2. Production (with Nginx): docker-compose -f docker-compose.production.yml up -d"
echo "3. Production (with monitoring): docker-compose -f docker-compose.production.yml --profile monitoring up -d"
echo "4. Traefik: docker-compose -f docker-compose.traefik.yml up -d"
echo ""
echo "📚 See MIDDLEWARE_SETUP.md for detailed configuration options"
