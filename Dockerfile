FROM python:3.11-slim

# Install system dependencies & curl for Ollama
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    procps \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama binary
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create non-root user (Hugging Face Spaces requirement: UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_NO_CLOUD=1

WORKDIR $HOME/app

# Copy dependency files
COPY --chown=user:user backend/requirements.txt ./backend/
COPY --chown=user:user frontend/package*.json ./frontend/

# Install Python requirements
RUN pip install --no-cache-dir --user -r ./backend/requirements.txt

# Pre-cache FastEmbed ONNX embedding model
RUN python -c "from fastembed import TextEmbedding; list(TextEmbedding('BAAI/bge-small-en-v1.5').embed(['init']))"

# Copy source code
COPY --chown=user:user . .

# Build Frontend
WORKDIR $HOME/app/frontend
RUN npm install && npm run build

WORKDIR $HOME/app

# Expose default Hugging Face Spaces port
EXPOSE 7860

# Make startup script executable and run
RUN chmod +x ./scripts/start_hf.sh
CMD ["./scripts/start_hf.sh"]
