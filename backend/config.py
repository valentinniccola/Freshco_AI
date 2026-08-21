import os
from pathlib import Path
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Freshco AI - Food Freshness Detection"
    SECRET_KEY: str = "freshco-super-secret-key-2026-fresh-detection"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'freshco.db'}"
    
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    STATIC_DIR: Path = BASE_DIR / "static"
    MODEL_DIR: Path = BASE_DIR / "ai" / "weights"

    # Gmail SMTP Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "valentinniccola@gmail.com"
    SMTP_USERNAME: Optional[str] = "valentinniccola@gmail.com"
    SMTP_PASSWORD: str = "dpqamzzmupzqybfw"
    EMAILS_FROM_NAME: str = "Freshco AI Security"
    RESET_CODE_EXPIRE_MINUTES: int = 10
    RESET_MAX_REQUESTS_PER_HOUR: int = 3

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def clean_smtp_fields(self):
        # Sync SMTP_USER and SMTP_USERNAME
        if self.SMTP_USERNAME and not self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USERNAME
        if self.SMTP_USER and not self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USER
            
        # Clean any whitespace from App Password
        if self.SMTP_PASSWORD:
            self.SMTP_PASSWORD = self.SMTP_PASSWORD.replace(" ", "").strip()
        if self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USER.strip()
        if self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USERNAME.strip()
        return self

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
