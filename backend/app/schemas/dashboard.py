"""Contrato do painel da tela inicial.

Reaproveita `MatchRead` e `RankingEntry`, que já existem desde a Fase 3 — o
mesmo dado não pode ter dois formatos dependendo de qual endpoint o devolve.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.match import MatchRead
from app.schemas.ranking import RankingEntry


class DashboardTotals(BaseModel):
    """Os três números grandes."""

    model_config = ConfigDict(from_attributes=True)

    matches_played: int = Field(
        validation_alias="matches_played", description="Partidas REALIZADAS na temporada"
    )
    goals_registered: int = Field(
        validation_alias="goals",
        description="Soma dos gols individuais lançados, não dos placares",
    )
    assists_registered: int = Field(validation_alias="assists")


class GoalsPointRead(BaseModel):
    """Um ponto da evolução de gols."""

    model_config = ConfigDict(from_attributes=True)

    match_date: dt.date
    goals: int


class DashboardRead(BaseModel):
    """Tudo o que a tela inicial precisa, numa resposta só."""

    season: int
    totals: DashboardTotals
    next_match: MatchRead | None = Field(
        description="Agendada mais próxima a partir de hoje. Fora do filtro de temporada."
    )
    last_match: MatchRead | None = Field(
        description="Realizada mais recente. Fora do filtro de temporada."
    )
    top_scorers: list[RankingEntry]
    top_assists: list[RankingEntry]
    goals_timeline: list[GoalsPointRead]
