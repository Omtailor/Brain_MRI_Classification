"""
Centralized application configuration.

Settings are read from environment variables (or a .env file via python-dotenv).
All defaults here are relative paths suitable for a local development setup.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend root (one level above app/)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_ROOT / ".env")


class Settings:
    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_TITLE: str = "Brain Tumor MRI Classification API"
    APP_VERSION: str = "3.0.0"
    APP_DESCRIPTION: str = (
        "FastAPI backend for brain tumor MRI classification. "
        "Part 3: Full pipeline — upload validation, Gemini MRI check, "
        "SmallCNN classification, and Gemini explanation."
    )

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    # Comma-separated list of allowed origins, e.g.
    # ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    ]

    # ------------------------------------------------------------------ #
    # CNN Model
    # ------------------------------------------------------------------ #
    # Path to the CNN checkpoint. Defaults to <backend_root>/models/cnn_baseline_best.pth
    MODEL_PATH: str = os.getenv(
        "MODEL_PATH",
        str(_BACKEND_ROOT / "models" / "cnn_baseline_best.pth"),
    )

    # Device override. When left empty the service auto-detects CUDA/CPU.
    DEVICE: str = os.getenv("DEVICE", "")

    # ------------------------------------------------------------------ #
    # Gemini
    # ------------------------------------------------------------------ #
    # Required. Set in .env or as an environment variable.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Gemini model identifier.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # ------------------------------------------------------------------ #
    # File uploads
    # ------------------------------------------------------------------ #
    # Maximum accepted upload size in megabytes.
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))

    # Derived byte limit — used directly in validation logic.
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:  # noqa: N802
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Allowed MIME types for uploads.
    ALLOWED_MIME_TYPES: dict[str, str] = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }

    # Allowed file extensions (lower-case).
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".pdf"}

    # ------------------------------------------------------------------ #
    # Server (informational — used by startup scripts, not by the app itself)
    # ------------------------------------------------------------------ #
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
