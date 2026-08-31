import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.db.session import engine, init_db
from backend.app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure local directory hierarchy and database schema are ready
    settings.ensure_directories()
    init_db(engine)
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sovereign On-Premise Agentic AI Workbench for Confidential Industrial Work",
    lifespan=lifespan
)

# CORS Policy: Permissive for on-premise local dev & Hugging Face container proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)

# Mount Frontend static build if available
frontend_dist = Path("frontend/dist")
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs_url": "/docs" if settings.DEBUG else "Disabled in Production Air-Gap"
        }

