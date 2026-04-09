from pathlib import Path
from typing import ClassVar
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = BASE_DIR

    GOOGLE_API_KEY: str | None = None
    RECURSION_LIMIT: int = 5
    MAX_FOLLOWUP_COUNT: int = 2

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        extra = 'ignore'


settings = Settings()
