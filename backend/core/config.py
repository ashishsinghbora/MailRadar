from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_FILE = PROJECT_ROOT / "mailradar.db"


class Settings(BaseSettings):
    app_name: str = "MailRadar"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "mailradar-super-secret-key-change-in-production-2026-secure"
    fernet_key: str = "Z3B2Q21RNGV2dmtIUVc2a2F1ckFvUTVwSG9XUlpVbmM="

    # Database (defaults to canonical project root SQLite file)
    database_url: str = f"sqlite:///{DEFAULT_DB_FILE}"

    # Redis & Workers
    redis_url: str = "redis://localhost:6379/0"

    # GitHub Integration
    github_api_token: Optional[str] = None

    # Delivery Provider
    delivery_provider: str = "sandbox"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "outreach@mailradar.dev"
    smtp_use_tls: bool = False

    # Security
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Rate limiting
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
