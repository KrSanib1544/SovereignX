# backend/app/config.py
"""
SOVEREIGN-X Configuration Module
Manages local-first application settings, database paths, and security boundaries.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # System metadata
    APP_NAME: str = "SOVEREIGN-X Core"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    AIRGAP_MODE: bool = True

    # Base directory paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    WORKSPACES_DIR: Path = DATA_DIR / "workspaces"
    AUDIT_LOG_DIR: Path = DATA_DIR / "audit_logs"
    QDRANT_STORAGE_DIR: Path = DATA_DIR / "qdrant_storage"

    # SQLite Database Configuration
    DATABASE_PATH: Path = DATA_DIR / "sovereign.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH.as_posix()}"
    ASYNC_DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH.as_posix()}"

    # Security Defaults
    DEFAULT_CLASSIFICATION: str = "INTERNAL_ENGINEERING"
    MAX_TASK_STEPS: int = 15
    TASK_TIMEOUT_SECONDS: int = 180
    SANDBOX_TIMEOUT_SECONDS: int = 30

    # Local Model Configurations (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    REASONING_MODEL: str = "qwen3:4b"
    VISION_MODEL: str = "gemma3:4b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Ensure all required local data directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
        self.AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.QDRANT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
