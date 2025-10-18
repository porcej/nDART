# Using Production Database with Docker

This guide explains how to connect your Dockerized nDART application to an existing production database.

## 🔧 **Database Connection Options**

### Option 1: SQLite Database File

If your production database is SQLite, you can mount it directly:

#### Step 1: Update docker-compose.yml
```yaml
volumes:
  # Replace the default database with your production database
  - /path/to/your/production/database.db:/app/db/app.db:ro  # Read-only
  # OR for read-write access:
  # - /path/to/your/production/database.db:/app/db/app.db
```

#### Step 2: Restart Container
```bash
docker-compose down
docker-compose up -d
```

### Option 2: PostgreSQL Database

#### Step 1: Update docker-compose.yml
```yaml
environment:
  - DATABASE_URL=postgresql://username:password@host:port/database_name
```

#### Step 2: Add PostgreSQL Client (if needed)
```dockerfile
# Add to Dockerfile if you need psql client
RUN apt-get update && apt-get install -y postgresql-client
```

#### Step 3: Restart Container
```bash
docker-compose down
docker-compose up -d
```

### Option 3: MySQL Database

#### Step 1: Update docker-compose.yml
```yaml
environment:
  - DATABASE_URL=mysql://username:password@host:port/database_name
```

#### Step 2: Add MySQL Client (if needed)
```dockerfile
# Add to Dockerfile if you need mysql client
RUN apt-get update && apt-get install -y mysql-client
```

#### Step 3: Restart Container
```bash
docker-compose down
docker-compose up -d
```

## 🔧 **Environment Variables Method**

### Using .env File

Create a `.env` file in your project root:

```bash
# .env file
DATABASE_URL=postgresql://username:password@your-db-host:5432/ndart_production
SECRET_KEY=your-production-secret-key
```

### Using Environment Variables

```bash
# Set environment variables
export DATABASE_URL="postgresql://username:password@your-db-host:5432/ndart_production"
export SECRET_KEY="your-production-secret-key"

# Start container
docker-compose up -d
```

## 🔧 **Docker Compose Override Method**

Create `docker-compose.override.yml`:

```yaml
version: '3.8'
services:
  ndart:
    environment:
      - DATABASE_URL=postgresql://username:password@your-db-host:5432/ndart_production
      - SECRET_KEY=your-production-secret-key
    volumes:
      # Remove local database mount
      - ./logs:/app/log
```

## 🔧 **Network Configuration**

### For Remote Databases

If your database is on a different server, ensure network connectivity:

```yaml
services:
  ndart:
    # ... other configuration
    extra_hosts:
      - "db-host:192.168.1.100"  # If using IP address
```

### For Database in Different Docker Network

```yaml
services:
  ndart:
    # ... other configuration
    external_links:
      - "production-db:db"
    environment:
      - DATABASE_URL=postgresql://username:password@db:5432/ndart_production
```

## 🔧 **Security Considerations**

### 1. Use Environment Variables for Secrets
```bash
# Never hardcode passwords in docker-compose.yml
DATABASE_URL=postgresql://username:${DB_PASSWORD}@host:port/database
```

### 2. Use Docker Secrets (Production)
```yaml
services:
  ndart:
    secrets:
      - db_password
    environment:
      - DATABASE_URL=postgresql://username:${DB_PASSWORD}@host:port/database

secrets:
  db_password:
    external: true
```

### 3. Use Read-Only Mounts for SQLite
```yaml
volumes:
  - /path/to/production.db:/app/db/app.db:ro  # Read-only for safety
```

## 🔧 **Testing Database Connection**

### Test Connection
```bash
# Test database connectivity
docker-compose exec ndart python -c "
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    try:
        db.session.execute(db.text('SELECT 1'))
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
"
```

### Check Health Endpoint
```bash
curl http://localhost:9091/health/database
```

## 🔧 **Common Issues and Solutions**

### Issue: Connection Refused
```bash
# Check if database host is reachable
docker-compose exec ndart ping your-db-host

# Check if port is open
docker-compose exec ndart telnet your-db-host 5432
```

### Issue: Authentication Failed
```bash
# Verify credentials
docker-compose exec ndart python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://username:password@host:port/database')
    print('✅ Authentication successful')
    conn.close()
except Exception as e:
    print(f'❌ Authentication failed: {e}')
"
```

### Issue: Database Not Found
```bash
# List available databases
docker-compose exec ndart python -c "
import psycopg2
conn = psycopg2.connect('postgresql://username:password@host:port/postgres')
cur = conn.cursor()
cur.execute('SELECT datname FROM pg_database')
print('Available databases:', [row[0] for row in cur.fetchall()])
"
```

## 🔧 **Production Deployment Examples**

### Example 1: PostgreSQL with Environment Variables
```bash
# Set environment variables
export DATABASE_URL="postgresql://ndart_user:secure_password@db.example.com:5432/ndart_production"
export SECRET_KEY="your-super-secure-secret-key"

# Start application
docker-compose up -d
```

### Example 2: SQLite with Production File
```bash
# Copy production database
cp /path/to/production/database.db ./db/app.db

# Start application
docker-compose up -d
```

### Example 3: MySQL with Docker Compose Override
```yaml
# docker-compose.override.yml
services:
  ndart:
    environment:
      - DATABASE_URL=mysql://ndart_user:secure_password@mysql.example.com:3306/ndart_production
      - SECRET_KEY=your-super-secure-secret-key
```

## 🔧 **Monitoring and Maintenance**

### Check Database Status
```bash
# Check health endpoint
curl http://localhost:9091/health/database

# Check application logs
docker-compose logs ndart
```

### Backup Production Database
```bash
# PostgreSQL backup
pg_dump -h your-db-host -U username -d database_name > backup.sql

# MySQL backup
mysqldump -h your-db-host -u username -p database_name > backup.sql

# SQLite backup
cp /path/to/production.db backup.db
```

## 🔧 **Troubleshooting Commands**

```bash
# Check container environment
docker-compose exec ndart env | grep DATABASE

# Check database connectivity
docker-compose exec ndart python -c "
from app import create_app
app = create_app()
print('Database URL:', app.config['SQLALCHEMY_DATABASE_URI'])
"

# Test database query
docker-compose exec ndart python -c "
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM users'))
    print('User count:', result.scalar())
"
```
