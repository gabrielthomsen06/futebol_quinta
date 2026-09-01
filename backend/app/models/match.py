"""Partida — data, status, os dois times e o placar."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, Index, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import EnumAsString
from app.models.enums import MATCH_STATUS_LENGTH, MatchStatus

if TYPE_CHECKING:
    from app.models.participation import MatchParticipation


class Match(Base, TimestampMixin):
    """Uma partida.

    Time não é entidade: uma partida sempre tem exatamente dois lados, e o
    lado não tem atributo nenhum além de nome e placar. Por isso os quatro
    campos moram aqui, e a participação guarda apenas o número do lado.

    Não existe UNIQUE em match_date — duas partidas podem dividir a mesma data.
    """

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    status: Mapped[MatchStatus] = mapped_column(
        EnumAsString(MatchStatus, MATCH_STATUS_LENGTH),
        nullable=False,
        server_default=MatchStatus.SCHEDULED.value,
    )
    team_1_name: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="TIME 1"
    )
    team_2_name: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="TIME 2"
    )
    # Placar fica nulo enquanto a partida não é realizada. Se a partida for
    # cancelada depois de ter placar, o valor permanece guardado e é
    # simplesmente ignorado nas estatísticas.
    team_1_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    team_2_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    participations: Mapped[list[MatchParticipation]] = relationship(
        back_populates="match",
        # Excluir a partida elimina o impacto dela em rankings, perfis
        # e dashboard. O banco cuida disso com ON DELETE CASCADE.
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('SCHEDULED', 'PLAYED', 'CANCELLED')",
            name="ck_matches_status",
        ),
        CheckConstraint(
            "(team_1_score IS NULL OR team_1_score >= 0)"
            " AND (team_2_score IS NULL OR team_2_score >= 0)",
            name="ck_matches_score_nao_negativo",
        ),
        # Partida realizada sem placar não pode existir: é do placar que saem
        # vitória, empate e derrota de todos os participantes.
        CheckConstraint(
            "status <> 'PLAYED'"
            " OR (team_1_score IS NOT NULL AND team_2_score IS NOT NULL)",
            name="ck_matches_played_tem_placar",
        ),
        CheckConstraint(
            "char_length(btrim(team_1_name)) > 0"
            " AND char_length(btrim(team_2_name)) > 0",
            name="ck_matches_nomes_nao_vazios",
        ),
        # Histórico e dashboard sempre leem do mais recente para o mais antigo.
        Index("ix_matches_date", text("match_date DESC")),
        Index("ix_matches_status_date", "status", text("match_date DESC")),
    )

    def __repr__(self) -> str:
        return f"<Match {self.match_date} {self.status.value}>"
