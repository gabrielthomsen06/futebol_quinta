"""Regras de negócio das estatísticas derivadas.

O repositório devolve os números brutos; aqui saem as médias, o aproveitamento
e a regra do piso de partidas nos rankings de média.
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import (
    AVERAGE_METRICS,
    MIN_GAMES_FOR_AVERAGE,
    PlayerStatus,
    RankingMetric,
)
from app.repositories import stats_repository
from app.repositories.stats_repository import PlayerMatchRow, PlayerStatsRow
from app.services import player_service


@dataclass(frozen=True, slots=True)
class PlayerStats:
    """Estatísticas de um jogador, brutas e derivadas."""

    player_id: uuid.UUID
    nickname: str
    photo_path: str | None
    status: PlayerStatus
    games: int
    goals: int
    assists: int
    wins: int
    draws: int
    losses: int
    goals_per_game: float
    assists_per_game: float
    win_rate: float
    goal_participations: int


def _derive(row: PlayerStatsRow) -> PlayerStats:
    """Acrescenta o que é calculado, protegendo contra divisão por zero."""
    games = row.games
    return PlayerStats(
        player_id=row.player_id,
        nickname=row.nickname,
        photo_path=row.photo_path,
        status=row.status,
        games=games,
        goals=row.goals,
        assists=row.assists,
        wins=row.wins,
        draws=row.draws,
        losses=row.losses,
        goals_per_game=round(row.goals / games, 2) if games else 0.0,
        assists_per_game=round(row.assists / games, 2) if games else 0.0,
        win_rate=round(row.wins / games * 100, 1) if games else 0.0,
        goal_participations=row.goals + row.assists,
    )


def players_with_stats(
    session: Session,
    *,
    statuses: Sequence[PlayerStatus] | None = None,
    search: str | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[PlayerStats]:
    """Todos os jogadores e suas estatísticas em uma consulta só."""
    rows = stats_repository.player_stats(
        session,
        statuses=statuses,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    return [_derive(row) for row in rows]


def player_stats(
    session: Session,
    player_id: uuid.UUID,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> PlayerStats:
    """Estatísticas de um jogador. Erro 404 se ele não existir."""
    player_service.get_player(session, player_id)
    rows = stats_repository.player_stats(
        session, player_id=player_id, date_from=date_from, date_to=date_to
    )
    return _derive(rows[0])


def player_match_history(
    session: Session,
    player_id: uuid.UUID,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[PlayerMatchRow]:
    return stats_repository.player_match_history(
        session, player_id, date_from=date_from, date_to=date_to
    )


def min_games_for(metric: RankingMetric) -> int:
    """O piso de 3 partidas vale só para os rankings de média.

    Gols, assistências, vitórias e jogos não têm piso: quem jogou uma vez e
    fez 3 gols merece aparecer na artilharia, só não pode liderar a média
    para sempre com 3,00.
    """
    return MIN_GAMES_FOR_AVERAGE if metric in AVERAGE_METRICS else 0


def ranking(
    session: Session,
    metric: RankingMetric,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int | None = None,
    min_games: int | None = None,
) -> list[PlayerStats]:
    """Ranking ordenado pela métrica, com desempate determinístico.

    Jogadores inativos continuam presentes: eles fizeram aqueles gols, e o
    histórico não muda porque alguém parou de jogar.
    """
    piso = min_games_for(metric) if min_games is None else min_games
    rows = stats_repository.player_stats(
        session,
        metric=metric,
        min_games=piso,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [_derive(row) for row in rows]
