"""Monta o painel da tela inicial.

Uma função, várias consultas, **uma resposta HTTP**: a tela inicial é a
primeira coisa que abre no celular e não pode custar seis requisições.

Nada aqui é contador guardado. Todos os números saem das partidas realizadas,
na hora, como em todo o resto do sistema.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import RankingMetric
from app.models.match import Match
from app.repositories import match_repository, stats_repository
from app.repositories.stats_repository import GoalsPoint, SeasonTotals
from app.services import stats_service
from app.services.stats_service import PlayerStats

TOP = 5


@dataclass(frozen=True, slots=True)
class Dashboard:
    season: int
    totals: SeasonTotals
    next_match: Match | None
    last_match: Match | None
    top_scorers: list[PlayerStats]
    top_assists: list[PlayerStats]
    goals_timeline: list[GoalsPoint]


def _periodo_da_temporada(season: int) -> tuple[dt.date, dt.date]:
    """A temporada é o ano da data da partida — sem entidade, sem tabela."""
    return dt.date(season, 1, 1), dt.date(season, 12, 31)


def _top(
    session: Session,
    metric: RankingMetric,
    *,
    date_from: dt.date,
    date_to: dt.date,
) -> list[PlayerStats]:
    """Os cinco primeiros de uma métrica, sem quem está zerado.

    O ranking completo devolve todo mundo, inclusive quem não marcou. Numa
    lista chamada ARTILHARIA, um jogador com 0 gols é ruído — ele aparece na
    página de Rankings, que é onde a lista completa vive.
    """
    entradas = stats_service.ranking(
        session, metric, date_from=date_from, date_to=date_to, limit=TOP
    )
    campo = "goals" if metric is RankingMetric.GOALS else "assists"
    return [e for e in entradas if getattr(e, campo) > 0]


def build(session: Session, *, season: int, today: dt.date) -> Dashboard:
    """Junta tudo o que a tela inicial mostra.

    Totais, rankings e a série do gráfico são **da temporada**. Próxima e
    última partida ficam de fora desse recorte: a próxima é sobre o futuro, e a
    última realizada interessa mesmo que tenha sido na temporada passada.
    """
    inicio, fim = _periodo_da_temporada(season)

    return Dashboard(
        season=season,
        totals=stats_repository.season_totals(session, date_from=inicio, date_to=fim),
        next_match=match_repository.next_scheduled(session, from_date=today),
        last_match=match_repository.last_played(session),
        top_scorers=_top(session, RankingMetric.GOALS, date_from=inicio, date_to=fim),
        top_assists=_top(session, RankingMetric.ASSISTS, date_from=inicio, date_to=fim),
        goals_timeline=stats_repository.goals_timeline(
            session, date_from=inicio, date_to=fim
        ),
    )
