# Stage 1: Build console frontend
FROM node:20-slim AS frontend
WORKDIR /app/console
COPY console/package*.json ./
RUN npm ci || npm install
COPY console/ ./
RUN npm run build

# Stage 2: Python 3.12 runtime
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/student \
    DATABASE_PATH=/data/codesentinel.db \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Copy built frontend assets from stage 1
COPY --from=frontend /app/console/dist /home/student/codesentinel-ai/console/dist
RUN mkdir -p /root/codesentinel-ai/console && \
    ln -s /home/student/codesentinel-ai/console/dist /root/codesentinel-ai/console/dist && \
    ln -s /home/student/codesentinel-ai/console/dist /app/console_dist

RUN mkdir -p /data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

CMD ["uvicorn", "codesentinel.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
