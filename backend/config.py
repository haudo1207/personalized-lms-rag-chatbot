from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchored to the project root so DB/vector-store/data paths don't silently
# change if uvicorn/streamlit is launched from a different working directory.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    database_url: str = f"sqlite:///{(BASE_DIR / 'app.db').as_posix()}"
    vector_db_path: str = str(BASE_DIR / "vector_store")
    raw_dir: str = str(BASE_DIR / "data" / "raw")
    processed_dir: str = str(BASE_DIR / "data" / "processed")
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 12 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
