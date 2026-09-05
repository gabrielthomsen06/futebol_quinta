"""Configuração da aplicação, lida exclusivamente do ambiente.

Nenhum segredo mora no código: tudo vem de variáveis de ambiente, que em
desenvolvimento chegam pelo .env da raiz via docker compose.

Em **produção** (`APP_ENV=production`) a configuração é validada no arranque e
a aplicação **recusa iniciar** se estiver insegura. Um site fora do ar chama
atenção na hora; um site no ar com a chave de exemplo do repositório, não.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PRODUCAO = "production"

# Valores que existem só para o desenvolvimento funcionar sem configuração.
# Qualquer um deles em produção é erro de deploy, não uma escolha.
SEGREDO_DE_DESENVOLVIMENTO = "inseguro-apenas-para-desenvolvimento"
_SENHAS_DE_EXEMPLO = frozenset(
    {"troque-esta-senha", "gere-uma-chave-aleatoria-e-longa", "changeme", "admin", "migue"}
)
TAMANHO_MINIMO_DA_CHAVE = 32

# O Heroku injeta DATABASE_URL no formato "postgres://" — um esquema que o
# SQLAlchemy 2.0 não conhece mais. E mesmo "postgresql://" cairia no psycopg2,
# que não é a dependência deste projeto. Por isso a URL é normalizada em
# execução, e não à mão: o Heroku reescreve a variável sozinho toda vez que
# rotaciona a credencial do banco.
_DRIVER = "postgresql+psycopg"
_ESQUEMAS_A_NORMALIZAR = ("postgres://", "postgresql://")


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
    # O plano Essential-0 do Heroku Postgres aceita ~20 conexões no total, e
    # cada worker do uvicorn tem o seu próprio pool. Com 2 workers, o teto
    # abaixo dá 2 x (3+2) = 10 conexões — sobra folga para a release phase,
    # para `heroku run` e para um psql aberto na mão.
    db_pool_size: int = 3
    db_max_overflow: int = 2

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
    # "local" grava em disco (desenvolvimento); "r2" grava no Cloudflare R2.
    # O padrão continua sendo o disco: quem muda isso é o ambiente do Heroku,
    # onde o sistema de arquivos do dyno é apagado a cada deploy e restart.
    storage_backend: str = "local"
    media_root: Path = Path("/app/media")
    media_url_prefix: str = "/media"
    max_photo_bytes: int = 5 * 1024 * 1024
    photo_size: int = 512

    # ---------- Cloudflare R2 (só quando storage_backend="r2") ----------
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    # Domínio público do bucket, se houver. Vazio faz a aplicação assinar uma
    # URL temporária a cada acesso — funciona com o bucket fechado, que é o
    # padrão seguro.
    r2_public_base_url: str = ""
    r2_url_expira_em: int = 3600

    # ---------- Frontend embutido ----------
    # Diretório com o React já compilado. Vazio (desenvolvimento) mantém a API
    # sozinha, com o Vite servindo o frontend em outra porta.
    static_root: Path | None = None

    # ---------- Proxy ----------
    # O roteador do Heroku termina o TLS e repassa em HTTP, então quem precisa
    # redirecionar para HTTPS é a aplicação, lendo o X-Forwarded-Proto.
    force_https: bool = False

    @field_validator("database_url", mode="after")
    @classmethod
    def _normalizar_url_do_banco(cls, url: str) -> str:
        """Aceita a URL como o Heroku a entrega e devolve a que o projeto usa.

        `sslmode=require` só é acrescentado quando o esquema veio como
        "postgres://", que na prática é a assinatura da variável injetada pelo
        Heroku. Sem isso, a negociação de TLS ficaria a cargo do padrão do
        psycopg (`prefer`), que aceitaria silenciosamente uma conexão em claro.
        """
        url = url.strip()
        for esquema in _ESQUEMAS_A_NORMALIZAR:
            if url.startswith(esquema):
                url = f"{_DRIVER}://{url[len(esquema):]}"
                if esquema == "postgres://" and "sslmode=" not in url:
                    separador = "&" if "?" in url else "?"
                    url = f"{url}{separador}sslmode=require"
                break
        return url

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

    @property
    def usa_r2(self) -> bool:
        return self.storage_backend.strip().lower() == "r2"

    @property
    def spa_dir(self) -> Path | None:
        """Diretório do React compilado, se ele existir de fato.

        Devolver None quando o caminho não existe evita que a aplicação suba
        com um mount apontando para o vazio — o sintoma seria um 404 em toda
        rota do frontend, difícil de ligar à causa.
        """
        if self.static_root is None:
            return None
        raiz = Path(self.static_root)
        return raiz if (raiz / "index.html").is_file() else None


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

    # Storage em disco num dyno do Heroku é uma armadilha silenciosa: funciona
    # no teste manual e some no deploy seguinte, deixando o banco apontando
    # para arquivos que não existem mais. Melhor não subir.
    if settings.usa_r2:
        faltando = [
            nome
            for nome, valor in (
                ("R2_ENDPOINT_URL", settings.r2_endpoint_url),
                ("R2_ACCESS_KEY_ID", settings.r2_access_key_id),
                ("R2_SECRET_ACCESS_KEY", settings.r2_secret_access_key),
                ("R2_BUCKET", settings.r2_bucket),
            )
            if not valor.strip()
        ]
        if faltando:
            problemas.append(
                f"STORAGE_BACKEND=r2 mas faltam: {', '.join(faltando)}."
            )

    if problemas:
        lista = "\n".join(f"  - {p}" for p in problemas)
        raise ConfiguracaoInsegura(
            "A aplicação recusou iniciar porque APP_ENV=production e a "
            f"configuração está insegura:\n{lista}\n"
            "Corrija a configuração do ambiente "
            "(.env.prod na VPS ou heroku config:set no Heroku) e suba novamente."
        )


@lru_cache
def get_settings() -> Settings:
    """Instância única — evita reler o ambiente a cada requisição."""
    settings = Settings()
    if settings.is_production:
        _validar_producao(settings)
    return settings


settings = get_settings()
