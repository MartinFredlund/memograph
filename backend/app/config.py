from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Two levels up: app/ → backend/ → project root
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    NEO4J_URI: str
    NEO4J_AUTH: SecretStr
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: SecretStr
    MINIO_ENDPOINT: str
    MINIO_BUCKET: str
    JWT_SECRET: SecretStr
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: SecretStr
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
