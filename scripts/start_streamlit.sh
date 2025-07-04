#!/bin/sh
# scripts/start_frontend.sh

echo "[frontend] Starting Streamlit frontend..."
exec streamlit run app_streamlit/Home.py --server.port 8501 --server.address 0.0.0.0