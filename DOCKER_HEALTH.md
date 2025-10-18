# Docker Health Check Integration

This document describes how to use the health endpoints with Docker for container health monitoring.

## Available Health Endpoints

### Main Health Endpoint
- **URL**: `/health`
- **Method**: GET
- **Description**: Comprehensive health check including database and external services
- **Returns**: 200 (healthy) or 503 (unhealthy)

### Readiness Check
- **URL**: `/health/ready`
- **Method**: GET  
- **Description**: Checks if application is ready to receive traffic
- **Returns**: 200 (ready) or 503 (not ready)

### Liveness Check
- **URL**: `/health/live`
- **Method**: GET
- **Description**: Minimal check to verify application is alive
- **Returns**: 200 (alive)

### Component-Specific Checks
- **Database**: `/health/database`
- **Staffer API**: `/health/staffer`

## Docker Integration

### Dockerfile Health Check

Add this to your Dockerfile:

```dockerfile
# Health check using the main health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:9091/health || exit 1
```

### Docker Compose Health Check

```yaml
version: '3.8'
services:
  ndart:
    build: .
    ports:
      - "9091:9091"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    environment:
      - DATABASE_URL=sqlite:///app/db/app.db
      - SECRET_KEY=your-secret-key
      - STAFFER_API_URL=http://staffer-api:8091/public-api/v1
      - STAFFER_API_ENABLED=true
```

### Kubernetes Health Checks

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ndart
spec:
  template:
    spec:
      containers:
      - name: ndart
        image: ndart:latest
        ports:
        - containerPort: 9091
        livenessProbe:
          httpGet:
            path: /health/live
            port: 9091
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 9091
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          value: "sqlite:///app/db/app.db"
        - name: SECRET_KEY
          value: "your-secret-key"
```

## Health Check Response Format

### Healthy Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "response_time": 0.123,
  "version": "0.0.1",
  "environment": "production",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful",
      "details": {
        "connection": true,
        "query_test": true,
        "user_count": 5
      }
    },
    "staffer_api": {
      "status": "healthy",
      "message": "Staffer API connection successful",
      "details": {
        "enabled": true,
        "url": "http://staffer-api:8091/public-api/v1",
        "response_time": 0.045,
        "status_code": 200
      }
    }
  }
}
```

### Unhealthy Response (503 Service Unavailable)
```json
{
  "status": "unhealthy",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "response_time": 2.456,
  "version": "0.0.1",
  "environment": "production",
  "components": {
    "database": {
      "status": "unhealthy",
      "message": "Database connection failed: connection refused",
      "details": {
        "connection": false,
        "error": "connection refused"
      }
    },
    "staffer_api": {
      "status": "unhealthy",
      "message": "Staffer API connection failed",
      "details": {
        "enabled": true,
        "url": "http://staffer-api:8091/public-api/v1",
        "error": "Connection error"
      }
    }
  }
}
```

## Testing Health Endpoints

### Using curl
```bash
# Test main health endpoint
curl -f http://localhost:9091/health

# Test readiness
curl -f http://localhost:9091/health/ready

# Test liveness
curl -f http://localhost:9091/health/live
```

### Using the test script
```bash
# Test all endpoints
python test_health.py

# Test against different server
python test_health.py http://your-server:9091
```

## Configuration

The health endpoints respect the following environment variables:

- `STAFFER_API_URL`: URL for the Staffer API
- `STAFFER_API_ENABLED`: Enable/disable Staffer API checks (true/false)
- `STAFFER_API_KEY`: API key for Staffer API authentication
- `DEBUG`: Affects the environment field in responses

## Best Practices

1. **Use appropriate endpoints**:
   - `/health/live` for liveness probes (minimal checks)
   - `/health/ready` for readiness probes (database connectivity)
   - `/health` for comprehensive monitoring

2. **Set appropriate timeouts**:
   - Liveness: 5-10 seconds
   - Readiness: 10-30 seconds
   - Health: 30-60 seconds

3. **Monitor response times**:
   - The `response_time` field helps identify performance issues
   - Set alerts for response times > 5 seconds

4. **Handle external dependencies**:
   - Staffer API checks are optional and won't fail the health check if disabled
   - Database connectivity is required for the application to be healthy
