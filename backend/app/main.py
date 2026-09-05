"""Ponto de entrada da API do SÓ NO MIGUÉ FC."""

import logging
import mimetypes

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    auth,
    dashboard,
    health,
    matches,
    media,
    players,
    rankings,
    seasons,
)
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import configurar_logs
from app.core.middleware import (
    ForceHTTPSMiddleware,
    SecurityHeadersMiddleware,
    SPAStaticFiles,
)
from app.core.security import secret_key_is_weak

configurar_logs()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API de estatísticas da pelada. Leitura é pública; "
        "escrita exige o administrador autenticado."
    ),
    # Fechados em producao: nao vazam dado e a escrita exige token, mas
    # entregam o mapa da API.
    docs_url="/docs" if settings.docs_habilitados else None,
    redoc_url="/redoc" if settings.docs_habilitados else None,
    openapi_url="/openapi.json" if settings.docs_habilitados else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A partir daqui, o que o Caddy fazia e o roteador do Heroku não faz.
# `add_middleware` empilha de dentro para fora: o último acrescentado é o
# primeiro a ver a requisição, e é por isso que o redirecionamento para HTTPS
# vem por último — nada deve acontecer antes dele.
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
if settings.force_https:
    app.add_middleware(ForceHTTPSMiddleware)

register_exception_handlers(app)

# Em produção, chave fraca já impediu o arranque em core.config. Aqui sobra
# apenas o aviso para quem desenvolve com o valor padrão.
if secret_key_is_weak():
    logger.warning(
        "SECRET_KEY fraca (valor padrão ou com menos de 32 caracteres). "
        "Gere uma com: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )

# Todas as rotas de negócio vivem sob /api. Os endpoints de escrita e o
# dashboard entram nas fases seguintes.
api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(players.router)
api_router.include_router(matches.router)
api_router.include_router(rankings.router)
api_router.include_router(seasons.router)
app.include_router(api_router)

# Mesmo health sem o prefixo, para o healthcheck do container e para o hábito
# de digitar /health direto. Fora do schema para não duplicar no Swagger.
app.include_router(health.router, include_in_schema=False)

# As fotos dos jogadores. Em desenvolvimento vêm do volume, servidas daqui
# mesmo; no Heroku vêm do Cloudflare R2, e a rota abaixo só redireciona — o
# banco continua guardando apenas o caminho relativo, nos dois casos.
if settings.usa_r2:
    app.include_router(media.router, prefix=settings.media_url_prefix)
else:
    settings.media_root.mkdir(parents=True, exist_ok=True)
    # Nem todo sistema conhece .webp; sem isto o StaticFiles serve as fotos
    # como application/octet-stream, e cache e proxies deixam de tratá-las
    # como imagem.
    mimetypes.add_type("image/webp", ".webp")
    app.mount(
        settings.media_url_prefix,
        StaticFiles(directory=settings.media_root),
        name="media",
    )

# O React compilado, quando ele vem junto na imagem (é o caso no Heroku, onde
# a aplicação é uma só). Montado por último de propósito: as rotas de API e de
# mídia já estão registradas e continuam ganhando desta.
_spa = settings.spa_dir

if _spa is None:

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/health",
        }

else:
    app.mount("/", SPAStaticFiles(_spa), name="spa")
