import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.config import settings
from backend.app.db.session import engine, init_db
from backend.app.main import app as fastapi_app

# Ensure directories and SQLite tables are initialized
settings.ensure_directories()
init_db(engine)

try:
    import gradio as gr
    
    with gr.Blocks(title="SOVEREIGN-X — Air-Gapped AI Workbench", theme=gr.themes.Base()) as demo:
        gr.Markdown(
            """
            # 🛡️ SOVEREIGN-X: Sovereign On-Premise Industrial AI Workbench
            **Air-Gapped • Cryptographic SHA-256 Audit Ledger • Dual-Class Execution Router • 100% Local RAG**
            """
        )
        gr.HTML(
            """
            <div style="width: 100%; height: 85vh; border-radius: 12px; overflow: hidden; border: 1px solid #1f2937;">
                <iframe src="/" style="width: 100%; height: 100%; border: none;"></iframe>
            </div>
            """
        )
    
    app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
except Exception:
    app = fastapi_app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
