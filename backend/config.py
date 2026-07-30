from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    database_url: str = "sqlite:///./app.db"
    vector_db_path: str = "./vector_store"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
