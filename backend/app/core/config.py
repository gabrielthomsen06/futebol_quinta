"""Configuração da aplicação, lida exclusivamente do ambiente.

Nenhum segredo mora no código: tudo vem de variáveis de ambiente, que em
desenvolvimento chegam pelo .env da raiz via docker compose.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Identificação ----------
    app_name: str = "SÓ NO MIGUÉ FC — API"
    app_version: str = "0.1.0"
    current_season: int = 2026

    # ---------- Banco ----------
    database_url: str = "postgresql+psycopg://migue:migue@db:5432/migue"

    # ---------- Segurança ----------
    secret_key: str = "inseguro-apenas-para-desenvolvimento"
    access_token_expire_minutes: int = 720
    admin_username: str = "admin"
    admin_password: str = "admin"

    # ---------- API ----------
    # Lista separada por vírgula. Nunca "*" em produção.
    cors_origins: str = "http://localhost:5173"

    # ---------- Fotos ----------
    media_root: Path = Path("/app/media")
    media_url_prefix: str = "/media"
    max_photo_bytes: int = 5 * 1024 * 1024
    photo_size: int = 512

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Instância única — evita reler o ambiente a cada requisição."""
    return Settings()


settings = get_settings()
