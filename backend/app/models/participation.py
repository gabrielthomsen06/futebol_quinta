"""Participação de um jogador numa partida, com o que ele fez nela."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.player import Player


class MatchParticipation(Base, TimestampMixin):
    """Quem jogou, de que lado, quantos gols e quantas assistências.

    Uma linha só para participação e estatística: separá-las seria uma relação
    1-para-1 obrigatória, ou seja, duas tabelas para a mesma coisa.
    """

    __tablename__ = "match_participations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # Excluir a partida apaga as estatísticas dela junto.
        ForeignKey("matches.id", ondelete="CASCADE", name="fk_participations_match"),
        nullable=False,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # O histórico protege o jogador: o banco recusa apagar quem já jogou.
        ForeignKey("players.id", ondelete="RESTRICT", name="fk_participations_player"),
        nullable=False,
    )
    # 1 = time 1, 2 = time 2. Aponta para team_1_name / team_2_name da partida.
    team: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    goals: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    assists: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    match: Mapped[Match] = relationship(back_populates="participations")
    player: Mapped[Player] = relationship(back_populates="participations")

    __table_args__ = (
        # Resolve duas regras de uma vez: o jogador não aparece duas vezes na
        # mesma partida e, por consequência, não pode estar nos dois times —
        # estar nos dois exigiria duas linhas com o mesmo par.
        UniqueConstraint("match_id", "player_id", name="uq_participations_match_player"),
        CheckConstraint("team IN (1, 2)", name="ck_participations_team"),
        CheckConstraint("goals >= 0", name="ck_participations_goals"),
        CheckConstraint("assists >= 0", name="ck_participations_assists"),
        Index("ix_participations_player", "player_id"),
    )

    def __repr__(self) -> str:
        return f"<MatchParticipation time={self.team} gols={self.goals}>"
