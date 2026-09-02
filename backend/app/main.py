"""Ponto de entrada da API do SÓ NO MIGUÉ FC."""

import logging
import mimetypes

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import auth, dashboard, health, matches, players, rankings, seasons
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.security import secret_key_is_weak

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API de estatísticas da pelada. Leitura é pública; "
        "escrita exige o administrador autenticado."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Alerta, não falha: travar a inicialização atrapalharia o desenvolvimento sem
# impedir nada de verdade. Em produção quem resolve é o gerenciador de segredos.
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

# As fotos dos jogadores são servidas do volume. Em produção isso passaria para
# um nginx/CDN sem tocar no banco, já que só o caminho relativo é persistido.
settings.media_root.mkdir(parents=True, exist_ok=True)
# Nem todo sistema conhece .webp; sem isto o StaticFiles serve as fotos como
# application/octet-stream, e cache e proxies deixam de tratá-las como imagem.
mimetypes.add_type("image/webp", ".webp")
app.mount(
    settings.media_url_prefix,
    StaticFiles(directory=settings.media_root),
    name="media",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
    }
