from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./vector_store")


@lru_cache
def get_settings() -> Settings:
    return Settings()

