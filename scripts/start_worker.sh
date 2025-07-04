#!/bin/sh
# scripts/start_worker.sh

echo "[worker] Fixing ownership of /app/uploads..."
chown -R appuser:appuser /app/uploads

echo "[worker] Starting Taskiq worker..."
exec taskiq worker app.core.taskiq_app:broker --log-level INFO --fs-discover