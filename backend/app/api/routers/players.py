"""Endpoints de jogadores.

Leitura é pública. Escrita exige o administrador, via AdminDep — a mesma
dependência única criada na Fase 4.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, File, Query, UploadFile, status

from app.api.deps import AdminDep, SessionDep
from app.models.enums import PlayerStatus
from app.schemas.player import (
    PlayerCreate,
    PlayerRead,
    PlayerStatisticsRead,
    PlayerStatsRead,
    PlayerStatusUpdate,
    PlayerUpdate,
)
from app.services import photo_service, player_service, stats_service

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


# --------------------------------------------------------------------------
# Escrita — exige o administrador. Não existe DELETE de jogador: quem sai do
# grupo é inativado, e o histórico continua intacto.
# --------------------------------------------------------------------------


@router.post(
    "",
    response_model=PlayerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um jogador",
    responses={409: {"description": "Já existe jogador com esse apelido"}},
)
def create_player(dados: PlayerCreate, session: SessionDep, admin: AdminDep) -> object:
    return player_service.create_player(session, nickname=dados.nickname)


@router.put(
    "/{player_id}",
    response_model=PlayerRead,
    summary="Edita o apelido",
    responses={409: {"description": "Já existe jogador com esse apelido"}},
)
def update_player(
    player_id: uuid.UUID, dados: PlayerUpdate, session: SessionDep, admin: AdminDep
) -> object:
    return player_service.update_player(session, player_id, nickname=dados.nickname)


@router.patch(
    "/{player_id}/status",
    response_model=PlayerRead,
    summary="Ativa ou inativa o jogador",
)
def set_player_status(
    player_id: uuid.UUID, dados: PlayerStatusUpdate, session: SessionDep, admin: AdminDep
) -> object:
    return player_service.set_status(session, player_id, dados.status)


@router.post(
    "/{player_id}/photo",
    response_model=PlayerRead,
    summary="Envia ou troca a foto",
    responses={400: {"description": "Arquivo grande demais, vazio ou não é imagem aceita"}},
)
def upload_player_photo(
    player_id: uuid.UUID,
    session: SessionDep,
    admin: AdminDep,
    foto: Annotated[UploadFile, File(description="JPEG, PNG ou WEBP, até 5 MB")],
) -> object:
    player = player_service.get_player(session, player_id)
    # UploadFile.file é síncrono, o que combina com os endpoints `def` deste
    # projeto — nada de misturar async só para ler um arquivo.
    return photo_service.store_player_photo(session, player, foto.file)


@router.delete(
    "/{player_id}/photo",
    response_model=PlayerRead,
    summary="Remove a foto",
)
def delete_player_photo(player_id: uuid.UUID, session: SessionDep, admin: AdminDep) -> object:
    player = player_service.get_player(session, player_id)
    return photo_service.remove_player_photo(session, player)
