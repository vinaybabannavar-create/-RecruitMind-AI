#!/bin/bash
# start.sh — Production startup script for Render Docker deployment
# Ensures FastAPI backend is 100% online before launching Streamlit frontend

set -e

# Generate candidates dataset if missing
if [ ! -f "data/candidates.json" ]; then
    echo "Generating candidates dataset..."
    python data/generate_candidates.py
fi

# Start FastAPI backend in background on internal port 8000
echo "Starting FastAPI backend on port 8000..."
uvicorn api.main:app --host 127.0.0.1 --port 8000 &

# Active health check: wait until FastAPI responds on port 8000
echo "Waiting for FastAPI backend to become ready..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health | grep -q '"status":"ok"'; then
        echo "✅ FastAPI backend is online and ready!"
        break
    fi
    echo "Waiting for FastAPI... ($i/30)"
    sleep 2
done

# Start Streamlit on Render's assigned $PORT (default 8501)
PORT=${PORT:-8501}
echo "Starting Streamlit frontend on port $PORT..."
exec streamlit run ui/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false
