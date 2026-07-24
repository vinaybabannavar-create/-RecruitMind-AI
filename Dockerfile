FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download AI embedding model into image layers so startup is instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy project files
COPY . .

# Generate candidates dataset
RUN python data/generate_candidates.py

# Expose Streamlit port (Render injects $PORT)
EXPOSE 8501

# Start FastAPI backend (internal on 8000) + Streamlit frontend on $PORT
CMD ["bash", "start.sh"]
