"""Jogador — apelido, foto e status. Nada além disso."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import EnumAsString
from app.models.enums import PLAYER_STATUS_LENGTH, PlayerStatus

if TYPE_CHECKING:
    from app.models.participation import MatchParticipation


class Player(Base, TimestampMixin):
    """Um jogador da pelada.

    Não existe contador agregado aqui — nem total_goals, nem total_assists,
    nem total_matches, nem total_wins. Toda estatística é derivada das
    partidas realizadas, o que mantém rankings e dashboard sempre coerentes
    com o histórico, mesmo depois de editar ou excluir uma partida.
    """

    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nickname: Mapped[str] = mapped_column(String(40), nullable=False)
    photo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PlayerStatus] = mapped_column(
        EnumAsString(PlayerStatus, PLAYER_STATUS_LENGTH),
        nullable=False,
        server_default=PlayerStatus.ACTIVE.value,
    )

    participations: Mapped[list[MatchParticipation]] = relationship(
        back_populates="player",
        # Sem cascade de exclusão: o histórico é justamente o que impede
        # apagar um jogador. Quem sai do grupo é inativado.
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_players_status",
        ),
        CheckConstraint(
            "char_length(btrim(nickname)) > 0",
            name="ck_players_nickname_nao_vazio",
        ),
        # Unicidade sem diferenciar caixa: não podem coexistir
        # "Gabriel" e "gabriel".
        Index("uq_players_nickname_lower", text("lower(nickname)"), unique=True),
        Index("ix_players_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Player {self.nickname} ({self.status.value})>"
