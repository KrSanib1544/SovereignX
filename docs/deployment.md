# SOVEREIGN-X — Deployment & Installation Runbook (Windows 11)

---

## 1. Prerequisites & Target Environment

- **Operating System**: Windows 11 64-bit (Build 22621 or higher)
- **CPU**: x86_64 Intel/AMD (4+ Cores)
- **RAM**: 16 GB Physical Memory
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4.0 GB VRAM)
- **NVIDIA Driver**: Version 610.62 (or higher) with CUDA UMD 13.3 support
- **Local Software**:
  1. **Python 3.11.x 64-bit** (Added to Windows PATH)
  2. **Node.js 20.x LTS & npm**
  3. **Docker Desktop for Windows** (WSL2 backend enabled, for micro-sandbox execution)
  4. **Ollama v0.33.1+** (Configured with `OLLAMA_NO_CLOUD=1`)

---

## 2. One-Time Setup & Asset Pre-Caching (Connected Phase)

Before entering the air-gapped facility, pre-download and cache all open-weight models and dependencies:

### Step 1: Pull Local LLM Weights into Ollama
```cmd
:: Configure Ollama for offline air-gap mode
setx OLLAMA_NO_CLOUD 1
setx OLLAMA_HOST 127.0.0.1:11434

:: Pull verified quantized 4B models
ollama pull qwen3:4b
ollama pull gemma3:4b
```

### Step 2: Pre-Cache FastEmbed ONNX Weights
```cmd
cd backend
python -c "from fastembed import TextEmbedding; list(TextEmbedding('BAAI/bge-small-en-v1.5').embed(['test']))"
```

### Step 3: Build the Hardened Docker Sandbox Image
```cmd
cd docker\sandbox-python
docker build -t sovereign-sandbox:1.0 .
```

### Step 4: Install Python & Node Dependencies
```cmd
:: Install backend requirements
cd ..\..\backend
pip install -r requirements.txt

:: Install frontend requirements
cd ..\frontend
npm install
npm run build
```

---

## 3. Air-Gapped Operation & Launch Runbook (Disconnected Phase)

1. **Disconnect Network**: Turn OFF Wi-Fi in Windows 11 Action Center and disconnect any Ethernet cables.
2. **Start Ollama Daemon**: Ensure Ollama is running in the Windows System Tray or launch via `ollama serve`.
3. **Launch SOVEREIGN-X**:
   Run the master launch script:
   ```cmd
   scripts\run_dev.bat
   ```
   *This starts:*
   - FastAPI Backend at `http://127.0.0.1:8000` (FastAPI + Uvicorn)
   - React Frontend at `http://127.0.0.1:5173` (Vite / Static Server)

4. **Access the Workbench**:
   Open Google Chrome / Microsoft Edge and navigate to `http://localhost:5173`.
   Confirm that the top header shows:
   `🟢 AIR-GAP ENFORCED (100% Sovereign) | GPU: RTX 3050 (4GB) | Model: Qwen3 4B (Ready)`

---

## 4. Troubleshooting Guide

| Issue / Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **CUDA OOM / Alloc error during vision task** | `qwen3:4b` and `gemma3:4b` loaded simultaneously. | In backend settings, verify `VRAM_SWAP_TIMEOUT=5`. Manually trigger `/api/v1/models/swap` or restart Ollama. |
| **Docker Sandbox Error: `ConnectionRefused`** | Docker Desktop is not running or WSL2 is stopped. | Start Docker Desktop from the Start Menu. If Docker is disabled by enterprise policy, enable `USE_SUBPROCESS_SANDBOX=true` in `.env`. |
| **OCR returns low confidence / blank text** | Scanned document resolution $< 150\text{ DPI}$. | Check image preprocessing filter; ensure grayscale conversion and contrast stretching are enabled. |
| **Slow token generation ($< 10\text{ tok/s}$)** | Ollama offloaded layers to CPU RAM due to high Windows VRAM usage. | Close background graphics software (games, Photoshop, 3D apps) to free up VRAM for CUDA context. |
