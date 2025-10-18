# Docker Setup for nDART

This document provides instructions for running the nDART application using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git (for cloning the repository)

## Quick Start

### 1. Clone and Navigate to Project
```bash
git clone <repository-url>
cd nDART
```

### 2. Set Environment Variables
Create a `.env` file in the project root:
```bash
# Required
SECRET_KEY=your-super-secret-key-change-this-in-production

# Optional - Staffer API Configuration
STAFFER_API_URL=http://staffer-api:8091/public-api/v1
STAFFER_API_KEY=your-staffer-api-key
STAFFER_API_ENABLED=false
```

### 3. Build and Run
```bash
# Build and start the application
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application
- **Application**: http://localhost:9091
- **Health Check**: http://localhost:9091/health

## Docker Commands

### Basic Operations
```bash
# Build the image
docker-compose build

# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f ndart

# Execute commands in container
docker-compose exec ndart bash
```

### Health Monitoring
```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect ndart-app | grep -A 10 Health

# Test health endpoint
curl http://localhost:9091/health
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key-change-this-in-production` | Flask secret key |
| `DATABASE_URL` | `sqlite:///app/db/app.db` | Database connection string |
| `FLASK_PORT` | `9091` | Application port |
| `MED_TRACKER_DEBUG` | `false` | Debug mode |
| `STAFFER_API_URL` | `http://staffer-api:8091/public-api/v1` | Staffer API URL |
| `STAFFER_API_KEY` | `` | Staffer API key |
| `STAFFER_API_ENABLED` | `false` | Enable Staffer API integration |

### Using Production Database

To connect to an existing production database, see [PRODUCTION_DATABASE.md](PRODUCTION_DATABASE.md) for detailed instructions.

**Quick Examples:**
```bash
# PostgreSQL
export DATABASE_URL="postgresql://username:password@host:port/database"

# MySQL  
export DATABASE_URL="mysql://username:password@host:port/database"

# SQLite file
cp /path/to/production.db ./db/app.db
```

### Volumes

- **`./db`**: Database files stored on host filesystem
- **`./logs`**: Application logs stored on host filesystem

### Ports

- **9091**: Main application port
- **8091**: Staffer API port (if enabled)

## Health Checks

The application includes comprehensive health checks:

### Endpoints
- **`/health`** - Full health check (database + external services)
- **`/health/ready`** - Readiness check
- **`/health/live`** - Liveness check
- **`/health/database`** - Database health
- **`/health/staffer`** - Staffer API health

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:9091/health || exit 1
```

## Development

### Local Development with Docker
```bash
# Run with development settings
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or set environment variables
MED_TRACKER_DEBUG=true docker-compose up
```

### Database Initialization
```bash
# Initialize database with all tables
docker-compose exec ndart python init_db.py

# Or run migrations (if available)
docker-compose exec ndart flask db upgrade

# Create new migration
docker-compose exec ndart flask db migrate -m "description"
```

### Debugging
```bash
# Access container shell
docker-compose exec ndart bash

# View application logs
docker-compose logs -f ndart

# Check health status
curl http://localhost:9091/health
```

## Production Deployment

### Security Considerations
1. **Change SECRET_KEY**: Use a strong, random secret key
2. **Use HTTPS**: Configure reverse proxy (nginx/traefik)
3. **Database**: Consider using PostgreSQL for production
4. **Volumes**: Use named volumes or external storage
5. **Networks**: Use custom networks for service isolation

### Production Environment Variables
```bash
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql://user:pass@db:5432/ndart
STAFFER_API_ENABLED=true
STAFFER_API_KEY=your-production-api-key
```

### Resource Limits
The docker-compose.yml includes resource limits:
- **Memory**: 512MB limit, 256MB reservation
- **CPU**: Default limits

Adjust based on your requirements.

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs ndart

# Check health status
docker inspect ndart-app | grep Health
```

#### Database Issues
```bash
# Reset database files
docker-compose down
# rm -rf db/* logs/*
docker-compose up --build

# Initialize database tables
docker-compose exec ndart python init_db.py

# Check database tables
docker-compose exec ndart python -c "
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    result = db.session.execute(db.text('SELECT name FROM sqlite_master WHERE type=\"table\"'))
    tables = [row[0] for row in result.fetchall()]
    print('Tables:', tables)
"
```

#### Health Check Failures
```bash
# Test health endpoint manually
curl -v http://localhost:9091/health

# Check container logs
docker-compose logs ndart
```

#### Port Conflicts
```bash
# Change port in docker-compose.yml
ports:
  - "9092:9091"  # Use port 9092 instead
```

### Logs and Monitoring
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs ndart
```

## Advanced Configuration

### Custom Docker Compose Override
Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  ndart:
    environment:
      - MED_TRACKER_DEBUG=true
    volumes:
      - ./local-config:/app/config
```

### Multi-Environment Setup
```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Support

For issues related to:
- **Docker**: Check Docker logs and health status
- **Application**: Check application logs and health endpoints
- **Database**: Verify database connectivity and migrations
- **External Services**: Check Staffer API configuration and connectivity
