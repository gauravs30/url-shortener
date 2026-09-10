"""Application settings, loaded from the environment (or a local .env file).

This module is a Phase-2 seam: in Docker/compose these come from `.env`, and in
Kubernetes the same names are populated from a ConfigMap + Secret.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # postgresql+asyncpg://user:pass@host:5432/dbname
    database_url: str = "postgresql+asyncpg://shortener:shortener@localhost:5432/shortener"

    # Public origin used to build the short URL returned to clients (no trailing slash).
    base_url: str = "http://localhost:8000"

    # Random short-code length (base62). 7 -> ~3.5e12 keyspace.
    short_code_length: int = 7

    # slowapi limit expression applied to link creation, per client IP.
    rate_limit: str = "20/minute"

    # Salt mixed into the SHA-256 of the client IP before storing a click row.
    ip_hash_salt: str = "change-me"

    # Echo SQL (dev only).
    sql_echo: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
