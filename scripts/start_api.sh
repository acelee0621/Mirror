#!/bin/sh
# scripts/start_api.sh

# 确保数据库迁移
./scripts/run_migrations.sh

echo "[app] Fixing ownership of /app/uploads..."
chown -R appuser:appuser /app/uploads

echo "[app] Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000