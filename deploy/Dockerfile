# GRANITE Vulcan Revenue Intelligence - SPCS Container
# Multi-stage build: React frontend + FastAPI backend

# =============================================================================
# Stage 1: Build React Frontend
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci --silent

COPY frontend/ ./

RUN npm run build

# =============================================================================
# Stage 2: Production Runtime
# =============================================================================
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

COPY deploy/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/log/nginx

RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== GRANITE VULCAN REVENUE INTELLIGENCE STARTUP ===" \n\
echo "Python version: $(python --version)" \n\
echo "Working directory: $(pwd)" \n\
echo "SNOWFLAKE_HOST: ${SNOWFLAKE_HOST:-NOT_SET}" \n\
echo "Token file exists: $(test -f /snowflake/session/token && echo YES || echo NO)" \n\
echo "Starting nginx..." \n\
nginx \n\
echo "Starting uvicorn..." \n\
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info \n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["/bin/bash", "/app/start.sh"]
