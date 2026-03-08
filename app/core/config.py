from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    jina_api_key: str = ""
    app_env: str = "development"
    app_port: int = 8000
    max_agent_iterations: int = 6
    fetch_timeout: int = 30
    max_content_chars: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()