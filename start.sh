#!/bin/bash
# start.sh — Resilient startup script for Render deployment

# 1. Ensure candidates dataset exists
if [ ! -f "data/candidates.json" ]; then
    echo "Generating candidates dataset..."
    python data/generate_candidates.py || true
fi

# 2. Start FastAPI backend in background on internal port 8000
echo "Starting FastAPI backend on port 8000..."
uvicorn api.main:app --host 127.0.0.1 --port 8000 &

# 3. Health check loop: wait until FastAPI responds 200 OK without crashing on connection refusal
echo "Waiting for FastAPI backend to initialize..."
for i in {1..30}; do
    RESPONSE=$(curl -s http://127.0.0.1:8000/health 2>/dev/null || echo "offline")
    if echo "$RESPONSE" | grep -q '"status":"ok"'; then
        echo "✅ FastAPI backend is online!"
        break
    fi
    echo "Backend starting up... ($i/30)"
    sleep 3
done

# 4. Start Streamlit on Render's assigned $PORT (default 8501)
PORT=${PORT:-8501}
echo "Starting Streamlit frontend on port $PORT..."
exec streamlit run ui/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false
