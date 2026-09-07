#!/bin/bash
set -e

echo "Starting nDART application..."

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    
    # Check if database file exists, if not create it
    if [ ! -f "/app/db/app.db" ]; then
        echo "Database file not found, creating new database..."
        mkdir -p /app/db
        touch /app/db/app.db
    fi
    
    # Run Flask database migrations
    echo "Executing: flask db upgrade"
    flask db upgrade
    
    echo "Database migrations completed successfully."
}

# Function to wait for database to be ready (for external databases)
wait_for_db() {
    if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]] || [[ "$DATABASE_URL" == mysql* ]]; then
        echo "Waiting for database to be ready..."
        # Add database connection check here if needed
        # For now, we'll assume the database is ready
    fi
}

# Function to start the application
start_app() {
    echo "Starting nDART application..."
    
    # Check if we should run in production mode
    if [ "$FLASK_ENV" = "production" ]; then
        echo "Starting in production mode with Gunicorn..."
        
        # Check if we have Gunicorn configuration from environment
        if [ -n "$GUNICORN_WORKERS" ] && [ -n "$GUNICORN_BIND" ]; then
            echo "Using custom Gunicorn configuration..."
            exec gunicorn \
                --bind "$GUNICORN_BIND" \
                --workers "${GUNICORN_WORKERS:-4}" \
                --threads "${GUNICORN_THREADS:-2}" \
                --timeout 120 \
                --keep-alive 5 \
                --max-requests 1000 \
                --max-requests-jitter 100 \
                --preload \
                wsgi:application
        else
            echo "Using default Gunicorn configuration..."
            exec gunicorn --bind 0.0.0.0:9091 --workers 4 --worker-class eventlet --worker-connections 1000 app:app
        fi
    else
        echo "Starting in development mode..."
        exec python app.py
    fi
}

# Main execution
main() {
    echo "nDART Docker Entrypoint Script"
    echo "=============================="
    
    # Wait for database if using external database
    wait_for_db
    
    # Run database migrations
    run_migrations
    
    # Start the application
    start_app
}

# Run main function
main "$@"
