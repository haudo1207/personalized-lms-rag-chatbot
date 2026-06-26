from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class Settings(BaseModel):
    gemini_api_key: str = GEMINI_API_KEY
    gemini_model: str = GEMINI_MODEL
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./vector_store")


@lru_cache
def get_settings() -> Settings:
    return Settings()
