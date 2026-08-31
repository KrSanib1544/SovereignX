#!/bin/bash
set -e

echo "=================================================="
echo "=== Starting Sovereign-X On Hugging Face Space ==="
echo "=================================================="

# 1. Start Ollama in background
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama daemon to initialize on localhost:11434..."
until curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "Ollama is active!"

# 2. Pull local quantized model
echo "Pulling local SLM weights (qwen3:4b)..."
ollama pull qwen3:4b || echo "Model weights ready"

# 3. Start FastAPI Application on Port 7860
echo "Launching FastAPI server on port 7860..."
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 7860
