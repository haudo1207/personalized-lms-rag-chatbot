from functools import lru_cache

import google.generativeai as genai

from backend.config import get_settings


def _has_configured_api_key() -> bool:
    api_key = get_settings().gemini_api_key
    return bool(api_key and api_key != "your_real_api_key")


@lru_cache(maxsize=1)
def get_gemini_model() -> genai.GenerativeModel:
    if not _has_configured_api_key():
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


def generate_answer(prompt: str) -> str:
    model = get_gemini_model()
    response = model.generate_content(prompt)
    return (response.text or "").strip()
