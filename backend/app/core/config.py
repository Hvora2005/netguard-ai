from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_ROOT / ".env"), extra="ignore")

    app_name: str = "NetGuard AI"
    api_prefix: str = "/api"

    database_url: str = "sqlite:///./netguard.db"
    secret_key: str = "change-me-to-a-random-string"
    cors_origins: str = "http://localhost:5173"

    model_storage_path: str = "./models_storage"
    upload_path: str = "./uploads"
    reports_path: str = "./reports"
    max_upload_size_mb: int = 200

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def resolve_path(self, relative: str) -> Path:
        path = (BACKEND_ROOT / relative).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
