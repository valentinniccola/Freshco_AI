import os
from pathlib import Path
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = bool(os.environ.get("VERCEL"))

# In Vercel serverless environment, only /tmp is writable
DEFAULT_UPLOAD_DIR = Path("/tmp/uploads") if IS_VERCEL else BASE_DIR / "uploads"
DEFAULT_DB_URL = "sqlite:////tmp/freshco.db" if IS_VERCEL else f"sqlite:///{BASE_DIR / 'freshco.db'}"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Freshco AI - Food Freshness Detection"
    SECRET_KEY: str = "freshco-super-secret-key-2026-fresh-detection"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    DATABASE_URL: str = Field(default_factory=lambda: os.environ.get("DATABASE_URL", DEFAULT_DB_URL))
    
    UPLOAD_DIR: Path = DEFAULT_UPLOAD_DIR
    STATIC_DIR: Path = BASE_DIR / "static"
    MODEL_DIR: Path = BASE_DIR / "ai" / "models"

    # Frontend URL for CORS configuration
    FRONTEND_URL: Optional[str] = None

    # Gmail SMTP Email Configuration (loaded strictly from environment / .env)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_NAME: str = "Freshco AI Security"
    RESET_CODE_EXPIRE_MINUTES: int = 10
    RESET_MAX_REQUESTS_PER_HOUR: int = 3

    # LLM API Configuration (Anthropic Claude)
    ANTHROPIC_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def clean_smtp_fields(self):
        if self.SMTP_USERNAME and not self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USERNAME
        if self.SMTP_USER and not self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USER
            
        if self.SMTP_PASSWORD:
            self.SMTP_PASSWORD = self.SMTP_PASSWORD.replace(" ", "").strip()
        if self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USER.strip()
        if self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USERNAME.strip()
        return self

settings = Settings()

# Ensure writable directories exist without throwing on read-only filesystem
try:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

try:
    if not IS_VERCEL:
        settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
