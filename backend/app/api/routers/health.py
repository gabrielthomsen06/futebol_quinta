"""Verificação de saúde: responde se a API está de pé e se o banco responde.

Serve a três propósitos — healthcheck do docker compose, diagnóstico manual e o
indicador de conectividade da tela inicial do frontend.
"""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep
from app.core.config import settings
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Saúde da API e do banco")
def health(session: SessionDep) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 — qualquer falha aqui significa banco fora
        logger.exception("Falha ao consultar o banco no /health")
        database = "erro"

    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        database=database,
        app=settings.app_name,
        version=settings.app_version,
        season=settings.current_season,
    )
