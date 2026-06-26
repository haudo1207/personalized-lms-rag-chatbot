from functools import lru_cache

import google.generativeai as genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL


def _has_configured_api_key() -> bool:
    return bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_real_api_key")


@lru_cache(maxsize=1)
def get_gemini_model() -> genai.GenerativeModel:
    if not _has_configured_api_key():
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)


def generate_answer(prompt: str) -> str:
    model = get_gemini_model()
    response = model.generate_content(prompt)
    return (response.text or "").strip()
