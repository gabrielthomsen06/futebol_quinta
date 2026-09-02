"""Rankings.

Público, como toda a leitura. Temporada, mês e intervalo livre viram um par de
datas **aqui no servidor**: o frontend manda o que a pessoa escolheu e não faz
aritmética de calendário.
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


@router.get(
    "",
    response_model=RankingRead,
    summary="Ranking por métrica",
    responses={400: {"description": "Recorte de período inválido ou combinado"}},
)
def get_ranking(
    session: SessionDep,
    metric: Annotated[
        RankingMetric, Query(description="Métrica de ordenação")
    ] = RankingMetric.GOALS,
    season: Annotated[
        int | None,
        Query(description="Ano inteiro. Exclusivo com month e com o intervalo de datas."),
    ] = None,
    month: Annotated[
        str | None,
        Query(description="AAAA-MM. Exclusivo com season e com o intervalo de datas."),
    ] = None,
    date_from: Annotated[
        dt.date | None, Query(description="Pode vir sozinho: 'de tal dia em diante'.")
    ] = None,
    date_to: Annotated[
        dt.date | None, Query(description="Pode vir sozinho: 'até tal dia'.")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RankingRead:
    inicio, fim = stats_service.resolver_periodo(
        season=season, month=month, date_from=date_from, date_to=date_to
    )

    # O piso de 3 partidas vale só nas duas métricas de média, e quem decide é
    # o service. A resposta devolve o valor para a tela poder explicá-lo.
    piso = stats_service.min_games_for(metric)
    entries = stats_service.ranking(
        session, metric, date_from=inicio, date_to=fim, limit=limit
    )

    return RankingRead(
        metric=metric,
        min_games=piso,
        date_from=inicio,
        date_to=fim,
        entries=[
            RankingEntry(
                position=i,
                player=PlayerStatsRead.model_validate(stats, from_attributes=True),
            )
            for i, stats in enumerate(entries, start=1)
        ],
    )
