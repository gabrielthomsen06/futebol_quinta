"""Ponto de entrada da API do SÓ NO MIGUÉ FC."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

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

# Todas as rotas de negócio vivem sob /api. Os routers de jogadores, partidas,
# rankings, dashboard e autenticação entram aqui nas fases seguintes.
api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
app.include_router(api_router)

# Mesmo health sem o prefixo, para o healthcheck do container e para o hábito
# de digitar /health direto. Fora do schema para não duplicar no Swagger.
app.include_router(health.router, include_in_schema=False)

# As fotos dos jogadores são servidas do volume. Em produção isso passaria para
# um nginx/CDN sem tocar no banco, já que só o caminho relativo é persistido.
settings.media_root.mkdir(parents=True, exist_ok=True)
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
