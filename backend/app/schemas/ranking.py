"""Contrato de saída dos rankings."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.models.enums import RankingMetric
from app.schemas.player import PlayerStatsRead


class RankingEntry(BaseModel):
    """Uma posição do ranking."""

    position: int = Field(ge=1)
    player: PlayerStatsRead


class RankingRead(BaseModel):
    """Ranking já ordenado pelo banco, com o recorte aplicado."""

    metric: RankingMetric
    min_games: int = Field(
        description="Piso de partidas realizadas; 3 nos rankings de média, 0 nos demais"
    )
    date_from: dt.date | None
    date_to: dt.date | None
    entries: list[RankingEntry]
