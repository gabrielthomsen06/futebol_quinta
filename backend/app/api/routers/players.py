"""Endpoints de leitura de jogadores.

A escrita (criar, editar, trocar status, foto) entra junto com a autenticação,
para nenhuma rota administrativa existir desprotegida "por enquanto".
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.models.enums import PlayerStatus
from app.schemas.player import (
    PlayerRead,
    PlayerStatisticsRead,
    PlayerStatsRead,
)
from app.services import player_service, stats_service

router = APIRouter(prefix="/players", tags=["jogadores"])

StatusFilter = Literal["active", "inactive", "all"]

_STATUS_MAP: dict[StatusFilter, list[PlayerStatus] | None] = {
    "active": [PlayerStatus.ACTIVE],
    "inactive": [PlayerStatus.INACTIVE],
    "all": None,
}


@router.get(
    "",
    response_model=list[PlayerRead] | list[PlayerStatsRead],
    summary="Lista jogadores",
)
def list_players(
    session: SessionDep,
    status: Annotated[
        StatusFilter,
        Query(description="Padrão: só ativos. Inativos continuam no histórico."),
    ] = "active",
    q: Annotated[str | None, Query(description="Busca por apelido")] = None,
    with_stats: Annotated[
        bool, Query(description="Traz jogos, gols e assistências na mesma consulta")
    ] = False,
) -> object:
    statuses = _STATUS_MAP[status]
    if with_stats:
        return stats_service.players_with_stats(session, statuses=statuses, search=q)
    return player_service.list_players(session, statuses=statuses, search=q)


@router.get("/{player_id}", response_model=PlayerRead, summary="Um jogador")
def get_player(session: SessionDep, player_id: uuid.UUID) -> object:
    return player_service.get_player(session, player_id)


@router.get(
    "/{player_id}/stats",
    response_model=PlayerStatisticsRead,
    summary="Estatísticas e histórico do jogador",
)
def get_player_stats(
    session: SessionDep,
    player_id: uuid.UUID,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> PlayerStatisticsRead:
    stats = stats_service.player_stats(
        session, player_id, date_from=date_from, date_to=date_to
    )
    history = stats_service.player_match_history(
        session, player_id, date_from=date_from, date_to=date_to
    )
    return PlayerStatisticsRead.model_validate(
        {"stats": stats, "history": history}, from_attributes=True
    )
