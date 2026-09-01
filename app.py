import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr
from backend.app.config import settings
from backend.app.db.session import engine, init_db
from backend.app.main import app as fastapi_app

# Initialize directories & database
settings.ensure_directories()
init_db(engine)

# Full-bleed CSS to render the authentic Sovereign-X UI edge-to-edge
custom_css = """
html, body, .gradio-container, .main, .app, #root {
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100vw !important;
    width: 100vw !important;
    height: 100vh !important;
    min-height: 100vh !important;
    overflow: hidden !important;
    background-color: #0B0F17 !important;
}
.gradio-container {
    padding: 0 !important;
    margin: 0 !important;
}
footer {
    display: none !important;
}
"""

with gr.Blocks(title="SOVEREIGN-X — Air-Gapped Agentic AI Workbench", css=custom_css) as demo:
    gr.HTML(
        """
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #0B0F17; z-index: 999999;">
            <iframe 
                src="/spa" 
                style="width: 100%; height: 100%; border: none; outline: none; margin: 0; padding: 0; display: block;"
                allow="clipboard-read; clipboard-write;"
            ></iframe>
        </div>
        """
    )

# Mount Gradio onto FastAPI root so HF Spaces detects it while serving the full React dashboard!
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    demo.launch()
