"""Temporadas disponíveis.

Existe para o seletor da tela de Rankings não ter 2026 chumbado no frontend.

**Não há entidade nem tabela de temporada**: uma temporada é o ano da
`match_date`, e a "corrente" é configuração da aplicação, lida do ambiente.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import extract, select

from app.api.deps import SessionDep
from app.core.config import settings
from app.models.match import Match
from app.schemas.season import SeasonsRead

router = APIRouter(prefix="/seasons", tags=["temporadas"])


@router.get("", response_model=SeasonsRead, summary="Temporadas com partidas")
def list_seasons(session: SessionDep) -> SeasonsRead:
    # Qualquer status conta: a pergunta aqui é "que anos existem no sistema",
    # não "quem pontuou". Um ano que só tem jogo agendado aparece no seletor e
    # mostra ranking vazio — que é a informação correta.
    ano = extract("year", Match.match_date)
    stmt = select(ano).distinct().order_by(ano.desc())

    return SeasonsRead(
        current=settings.current_season,
        available=[int(linha[0]) for linha in session.execute(stmt)],
    )
