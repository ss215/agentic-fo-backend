#!/bin/bash

# Agentic F&O Backend Startup Script
# This script handles database initialization and starts the application

echo "🚀 Starting Agentic F&O Backend..."

# Wait for database to be ready (if using external database)
if [ ! -z "$DATABASE_URL" ]; then
    echo "📊 Waiting for database connection..."
    python -c "
import time
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('✅ Database connection successful!')
        break
    except OperationalError as e:
        retry_count += 1
        print(f'⏳ Database not ready, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        break
else:
    print('⚠️ No DATABASE_URL provided, skipping database connection test')
    print('ℹ️ Application will start without database connection')
"
fi

# Initialize database tables
echo "🗄️ Initializing database tables..."
python -c "
try:
    from database.connection import create_tables
    create_tables()
    print('✅ Database tables created successfully!')
except Exception as e:
    print(f'⚠️ Database initialization warning: {e}')
    print('Continuing with startup...')
"

# Start the application
echo "🎯 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
