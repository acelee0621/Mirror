#!/bin/sh


echo "[alembic] PostgreSQL is ready, running migrations..."
alembic upgrade head || { echo "[alembic] Migration failed"; exit 1; }