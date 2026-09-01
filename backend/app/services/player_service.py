"""Regras de negócio de jogadores."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import transaction
from app.models.enums import PlayerStatus
from app.models.player import Player
from app.repositories import player_repository


def list_players(
    session: Session,
    *,
    statuses: Sequence[PlayerStatus] | None = None,
    search: str | None = None,
) -> list[Player]:
    return player_repository.list_players(session, statuses=statuses, search=search)


def get_player(session: Session, player_id: uuid.UUID) -> Player:
    player = player_repository.get_player(session, player_id)
    if player is None:
        raise NotFoundError("Jogador não encontrado.")
    return player


def create_player(
    session: Session, *, nickname: str, status: PlayerStatus = PlayerStatus.ACTIVE
) -> Player:
    """Cria o jogador, recusando apelido já usado.

    A checagem antecipada existe para o erro chegar como mensagem legível em
    vez de estouro de constraint — o índice único continua sendo a garantia
    final, inclusive contra duas requisições simultâneas.
    """
    nickname = nickname.strip()
    _ensure_nickname_livre(session, nickname)

    player = Player(nickname=nickname, status=status)
    with transaction(session):
        player_repository.add(session, player)
    session.refresh(player)
    return player


def update_player(session: Session, player_id: uuid.UUID, *, nickname: str) -> Player:
    player = get_player(session, player_id)
    nickname = nickname.strip()
    _ensure_nickname_livre(session, nickname, ignorar_id=player.id)

    with transaction(session):
        player.nickname = nickname
    session.refresh(player)
    return player


def set_status(session: Session, player_id: uuid.UUID, status: PlayerStatus) -> Player:
    """Ativa ou inativa.

    Inativar não apaga nada: o jogador continua no histórico, nos rankings e
    com perfil próprio. A única diferença é ficar fora da seleção padrão de
    participantes de uma nova partida.
    """
    player = get_player(session, player_id)
    with transaction(session):
        player.status = status
    session.refresh(player)
    return player


def _ensure_nickname_livre(
    session: Session, nickname: str, *, ignorar_id: uuid.UUID | None = None
) -> None:
    existente = player_repository.get_by_nickname(session, nickname)
    if existente is not None and existente.id != ignorar_id:
        raise ConflictError(f'Já existe um jogador com o apelido "{existente.nickname}".')
