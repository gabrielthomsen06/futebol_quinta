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
        description=(
            "Piso adicional de partidas exigido pela métrica: 3 nas médias, 0 nas demais. "
            "Independente disso, o ranking sempre lista apenas quem tem ao menos uma "
            "partida realizada no período."
        )
    )
    date_from: dt.date | None
    date_to: dt.date | None
    entries: list[RankingEntry]
