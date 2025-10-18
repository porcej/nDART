# Quick Database Setup Guide

## 🚀 **Quick Setup for Production Database**

### SQLite Database File
```bash
# Copy your production database
cp /path/to/your/production.db ./db/app.db

# Start the application
docker-compose up -d
```

### PostgreSQL Database
```bash
# Set environment variable
export DATABASE_URL="postgresql://username:password@your-host:5432/database_name"

# Start the application
docker-compose up -d
```

### MySQL Database
```bash
# Set environment variable
export DATABASE_URL="mysql://username:password@your-host:3306/database_name"

# Start the application
docker-compose up -d
```

## 🔧 **Using .env File**

Create `.env` file:
```bash
DATABASE_URL=postgresql://username:password@your-host:5432/database_name
SECRET_KEY=your-production-secret-key
```

## 🔧 **Docker Compose Override**

Create `docker-compose.override.yml`:
```yaml
services:
  ndart:
    environment:
      - DATABASE_URL=postgresql://username:password@your-host:5432/database_name
```

## ✅ **Test Connection**

```bash
# Test database connection
curl http://localhost:9091/health/database

# Check application logs
docker-compose logs ndart
```

## 🔧 **Common Database URLs**

| Database | URL Format |
|----------|------------|
| SQLite | `sqlite:///path/to/database.db` |
| PostgreSQL | `postgresql://user:pass@host:port/db` |
| MySQL | `mysql://user:pass@host:port/db` |
| SQL Server | `mssql+pyodbc://user:pass@host:port/db` |

## 🚨 **Security Notes**

- Never hardcode passwords in docker-compose.yml
- Use environment variables for sensitive data
- Consider using Docker secrets for production
- Use read-only mounts for SQLite files when possible
