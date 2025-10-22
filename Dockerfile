# Backend + Frontend (static served by Flask) container
FROM python:3.11-slim

# Install system deps (optional: for mysqlclient, but we use PyMySQL which is pure Python)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install python dependencies first (cache layer)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy app source
COPY . .

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Environment (can be overridden by docker-compose)
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    MYSQL_HOST=mysql \
    MYSQL_PORT=3306 \
    MYSQL_USER=root \
    MYSQL_PASSWORD=root \
    MYSQL_DATABASE=cgv_streaming

# Expose port
EXPOSE 5000

# Start both Flask app and auto-importer
CMD ["/docker-entrypoint.sh"]
