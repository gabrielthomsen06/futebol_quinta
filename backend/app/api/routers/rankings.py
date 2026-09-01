"""Endpoint de rankings.

A página completa, com filtros de temporada e mês, é da Fase 9. Aqui existe o
essencial para provar a consulta agregada contra dados reais.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.models.enums import RankingMetric
from app.schemas.player import PlayerStatsRead
from app.schemas.ranking import RankingEntry, RankingRead
from app.services import stats_service

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("", response_model=RankingRead, summary="Ranking por métrica")
def get_ranking(
    session: SessionDep,
    metric: Annotated[
        RankingMetric, Query(description="Métrica de ordenação")
    ] = RankingMetric.GOALS,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RankingRead:
    piso = stats_service.min_games_for(metric)
    entries = stats_service.ranking(
        session, metric, date_from=date_from, date_to=date_to, limit=limit
    )
    return RankingRead(
        metric=metric,
        min_games=piso,
        date_from=date_from,
        date_to=date_to,
        entries=[
            RankingEntry(
                position=i,
                player=PlayerStatsRead.model_validate(stats, from_attributes=True),
            )
            for i, stats in enumerate(entries, start=1)
        ],
    )
