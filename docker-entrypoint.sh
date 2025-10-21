#!/bin/bash
# Entrypoint script to run Flask app and importer

# Start Flask app in background
python backend/app.py &

# Wait 10 seconds for Flask to initialize
sleep 10

# Start continuous importer (every 3 minutes)
python backend/scripts/ophim_import_v3.py --continuous --interval 3 --check-update &

# Keep container running
wait
