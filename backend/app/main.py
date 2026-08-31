# backend/app/main.py
"""
SOVEREIGN-X Backend Application Entrypoint
FastAPI application configured for local offline execution with telemetry and model routing.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# CORS Policy: Restrict strictly to localhost/127.0.0.1 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else "Disabled in Production Air-Gap"
    }
