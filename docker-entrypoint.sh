#!/bin/bash#!/bin/sh

set -e# Entrypoint script to run Flask app and importer



echo "======================================================================"echo "🚀 Starting Flask app..."

echo "🎬  CGV STREAMING - MOVIE PLATFORM"# Start Flask app in background

echo "======================================================================"python backend/app.py &

FLASK_PID=$!

# Wait for MySQL to be ready

echo "⏳ Waiting for MySQL to be ready..."# Wait 15 seconds for Flask to initialize

while ! nc -z mysql 3306; doecho "⏳ Waiting for Flask to initialize..."

  sleep 1sleep 15

done

echo "✅ MySQL is ready!"# Setup FULLTEXT indexes (if not already created)

echo "🔍 Setting up FULLTEXT indexes for search optimization..."

# Initialize databasepython backend/scripts/setup_fulltext_indexes.py

echo "🚀 Initializing database..."

cd /appecho "🔄 Starting continuous importer (every 3 minutes)..."

python3 -c "# Start continuous importer (every 3 minutes)

from backend.db_manager import DatabaseConnectionpython backend/scripts/ophim_import_v3.py --continuous --interval 3 --check-update &

db = DatabaseConnection()IMPORTER_PID=$!

print('✅ Database initialized successfully!')

"echo "✅ Both services started:"

echo "   - Flask PID: $FLASK_PID"

# Setup fulltext indexesecho "   - Importer PID: $IMPORTER_PID"

echo "🔍 Setting up fulltext indexes..."

python3 backend/scripts/setup_fulltext_indexes.py# Keep container running and monitor both processes

wait -n

echo ""

echo "🌐 Starting Flask server..."# If any process exits, exit container

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"exit $?

echo "🚀 Server Status: ONLINE"

echo "🔗 Main URL:      http://localhost:5000"
echo "🔐 Login Page:    http://localhost:5000/login.html"
echo "🎥 Movies Page:   http://localhost:5000/streaming.html"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Press CTRL+C to stop the server"
echo "======================================================================"
echo ""

# Start Flask application
exec python3 backend/app.py
