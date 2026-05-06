from pathlib import Path
from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = BASE_DIR

    GOOGLE_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra='ignore',
    )


settings = Settings()
