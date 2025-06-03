from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALLURE_RESULTS_DIR: str = "allure-html"
    SERVER_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()
