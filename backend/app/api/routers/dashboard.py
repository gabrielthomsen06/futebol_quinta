"""Painel da tela inicial.

Público, como todo o resto da leitura. Uma requisição devolve o painel inteiro
— internamente são várias consultas, mas quem abre o site no celular faz uma
chamada só.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.core.config import settings
from app.schemas.dashboard import DashboardRead, DashboardTotals, GoalsPointRead
from app.schemas.match import MatchRead
from app.schemas.player import PlayerStatsRead
from app.schemas.ranking import RankingEntry
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead, summary="Painel da tela inicial")
def get_dashboard(
    session: SessionDep,
    season: Annotated[
        int | None,
        Query(ge=2000, le=2100, description="Ano da temporada. Padrão: a temporada corrente."),
    ] = None,
) -> DashboardRead:
    painel = dashboard_service.build(
        session,
        season=season or settings.current_season,
        # A data local do servidor, que roda em America/Sao_Paulo.
        today=dt.date.today(),
    )

    def posicoes(entradas: list) -> list[RankingEntry]:
        return [
            RankingEntry(
                position=i,
                player=PlayerStatsRead.model_validate(stats, from_attributes=True),
            )
            for i, stats in enumerate(entradas, start=1)
        ]

    return DashboardRead(
        season=painel.season,
        totals=DashboardTotals.model_validate(painel.totals, from_attributes=True),
        next_match=MatchRead.model_validate(painel.next_match) if painel.next_match else None,
        last_match=MatchRead.model_validate(painel.last_match) if painel.last_match else None,
        top_scorers=posicoes(painel.top_scorers),
        top_assists=posicoes(painel.top_assists),
        goals_timeline=[
            GoalsPointRead.model_validate(p, from_attributes=True)
            for p in painel.goals_timeline
        ],
    )
