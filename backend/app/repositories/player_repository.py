"""Acesso a dados de jogadores. Sem regra de negócio e sem commit."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PlayerStatus
from app.models.player import Player


def list_players(
    session: Session,
    *,
    statuses: Sequence[PlayerStatus] | None = None,
    search: str | None = None,
) -> list[Player]:
    """Jogadores ordenados por apelido, com filtro de status e busca."""
    stmt = select(Player)
    if statuses:
        stmt = stmt.where(Player.status.in_(list(statuses)))
    if search:
        stmt = stmt.where(Player.nickname.ilike(f"%{search.strip()}%"))
    stmt = stmt.order_by(Player.nickname.asc())
    return list(session.scalars(stmt))


def get_player(session: Session, player_id: uuid.UUID) -> Player | None:
    return session.get(Player, player_id)


def get_by_nickname(session: Session, nickname: str) -> Player | None:
    """Busca sem diferenciar maiúsculas, para checar duplicidade.

    Usa a mesma expressão do índice único uq_players_nickname_lower, então a
    consulta aproveita o índice em vez de varrer a tabela.
    """
    stmt = select(Player).where(func.lower(Player.nickname) == nickname.strip().lower())
    return session.scalars(stmt).first()


def add(session: Session, player: Player) -> Player:
    session.add(player)
    session.flush()
    return player


# Não existe remover jogador: o histórico é preservado e quem sai do grupo
# é inativado. A ausência da função é proposital.
