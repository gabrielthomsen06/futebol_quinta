"""Configuração da aplicação, lida exclusivamente do ambiente.

Nenhum segredo mora no código: tudo vem de variáveis de ambiente, que em
desenvolvimento chegam pelo .env da raiz via docker compose.

Em **produção** (`APP_ENV=production`) a configuração é validada no arranque e
a aplicação **recusa iniciar** se estiver insegura. Um site fora do ar chama
atenção na hora; um site no ar com a chave de exemplo do repositório, não.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PRODUCAO = "production"

# Valores que existem só para o desenvolvimento funcionar sem configuração.
# Qualquer um deles em produção é erro de deploy, não uma escolha.
SEGREDO_DE_DESENVOLVIMENTO = "inseguro-apenas-para-desenvolvimento"
_SENHAS_DE_EXEMPLO = frozenset(
    {"troque-esta-senha", "gere-uma-chave-aleatoria-e-longa", "changeme", "admin", "migue"}
)
TAMANHO_MINIMO_DA_CHAVE = 32


class ConfiguracaoInsegura(RuntimeError):
    """Produção com configuração faltando ou com valor de exemplo."""


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

    # ---------- Ambiente ----------
    app_env: str = "development"
    log_level: str = "INFO"

    # ---------- Banco ----------
    database_url: str = "postgresql+psycopg://migue:migue@db:5432/migue"

    # ---------- Segurança ----------
    secret_key: str = SEGREDO_DE_DESENVOLVIMENTO
    access_token_expire_minutes: int = 720
    admin_username: str = "admin"
    # ADMIN_PASSWORD não aparece aqui de propósito: só o comando create-admin a
    # usa, lendo o ambiente diretamente. Mantê-la como campo com valor padrão
    # criaria uma senha fraca que ninguém lê — e impediria removê-la do .env
    # depois que o administrador já existe, que é a recomendação.

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

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == PRODUCAO

    @property
    def docs_habilitados(self) -> bool:
        """Swagger e ReDoc só fora de produção.

        Não vazam dado e a escrita exige token, mas entregam o mapa da API —
        e em produção quem precisa deles é quem já tem o ambiente de
        desenvolvimento.
        """
        return not self.is_production


def _validar_producao(settings: Settings) -> None:
    """Recusa subir com configuração insegura. Sem meio-termo, sem aviso.

    Valida apenas o que a **aplicação** consome. A senha do administrador não
    entra aqui: quem a valida é o `create-admin`, com a política de senha —
    e ela deve poder sair do ambiente depois que o admin existe.
    """
    problemas: list[str] = []

    chave = settings.secret_key.strip()
    if not chave or chave == SEGREDO_DE_DESENVOLVIMENTO or chave in _SENHAS_DE_EXEMPLO:
        problemas.append(
            "SECRET_KEY está ausente ou com o valor de exemplo. "
            'Gere uma: python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    elif len(chave) < TAMANHO_MINIMO_DA_CHAVE:
        problemas.append(
            f"SECRET_KEY tem {len(chave)} caracteres; o mínimo é {TAMANHO_MINIMO_DA_CHAVE}."
        )

    url = settings.database_url.strip()
    if not url:
        problemas.append("DATABASE_URL está ausente.")
    elif any(f":{exemplo}@" in url for exemplo in _SENHAS_DE_EXEMPLO):
        problemas.append("DATABASE_URL usa uma senha de exemplo. Troque a senha do banco.")

    if not settings.cors_origins_list:
        problemas.append("CORS_ORIGINS está vazia. Informe a origem pública do site.")
    elif "*" in settings.cors_origins:
        problemas.append('CORS_ORIGINS não pode ser "*" em produção.')

    if problemas:
        lista = "\n".join(f"  - {p}" for p in problemas)
        raise ConfiguracaoInsegura(
            "A aplicação recusou iniciar porque APP_ENV=production e a "
            f"configuração está insegura:\n{lista}\n"
            "Corrija o .env.prod e suba de novo."
        )


@lru_cache
def get_settings() -> Settings:
    """Instância única — evita reler o ambiente a cada requisição."""
    settings = Settings()
    if settings.is_production:
        _validar_producao(settings)
    return settings


settings = get_settings()
