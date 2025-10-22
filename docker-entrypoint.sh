#!/bin/sh
# Entrypoint script to run Flask app and importer

echo "🚀 Starting Flask app..."
# Start Flask app in background
python backend/app.py &
FLASK_PID=$!

# Wait 15 seconds for Flask to initialize
echo "⏳ Waiting for Flask to initialize..."
sleep 15

# Setup FULLTEXT indexes (if not already created)
echo "🔍 Setting up FULLTEXT indexes for search optimization..."
python backend/scripts/setup_fulltext_indexes.py

echo "🔄 Starting continuous importer (every 3 minutes)..."
# Start continuous importer (every 3 minutes)
python backend/scripts/ophim_import_v3.py --continuous --interval 3 --check-update &
IMPORTER_PID=$!

echo "✅ Both services started:"
echo "   - Flask PID: $FLASK_PID"
echo "   - Importer PID: $IMPORTER_PID"

# Keep container running and monitor both processes
wait -n

# If any process exits, exit container
exit $?

