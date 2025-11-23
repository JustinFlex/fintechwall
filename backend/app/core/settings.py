"""Application configuration powered by pydantic settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings."""

    data_mode: Literal["wind", "open", "mock"] = "mock"
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False
    snapshot_cache_ttl: int = 15
    api_title: str = "Wind Market Wallboard API"
    api_version: str = "0.1.0"
    alphavantage_api_key: str = "demo"

    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
