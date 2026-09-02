"""Contratos de entrada e saída de jogadores."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PlayerStatus


class PlayerRead(BaseModel):
    """Jogador sem estatísticas."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nickname: str
    photo_path: str | None
    status: PlayerStatus
    created_at: dt.datetime
    updated_at: dt.datetime


class PlayerStatsRead(BaseModel):
    """Jogador com as estatísticas derivadas das partidas realizadas."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(validation_alias="player_id")
    nickname: str
    photo_path: str | None
    status: PlayerStatus

    games: int = Field(description="Partidas REALIZADAS em que participou")
    goals: int
    assists: int
    wins: int
    draws: int
    losses: int

    goals_per_game: float
    assists_per_game: float
    win_rate: float = Field(description="Percentual de vitórias, de 0 a 100")
    goal_participations: int = Field(description="Gols + assistências")


class PlayerMatchRead(BaseModel):
    """Uma partida no histórico individual do jogador."""

    model_config = ConfigDict(from_attributes=True)

    match_id: uuid.UUID
    match_date: dt.date
    team_1_name: str
    team_2_name: str
    team_1_score: int
    team_2_score: int
    team: int = Field(description="Lado em que o jogador estava: 1 ou 2")
    goals: int
    assists: int
    result: str = Field(description="V, E ou D, do ponto de vista do jogador")


class PlayerStatisticsRead(BaseModel):
    """Resposta de GET /api/players/{id}/stats."""

    stats: PlayerStatsRead
    history: list[PlayerMatchRead]


class PlayerCreate(BaseModel):
    """Corpo de POST /api/players.

    Só o apelido: nem posição, nem número, nem idade. A foto vem depois, por
    upload próprio.
    """

    nickname: str = Field(min_length=1, max_length=40)


class PlayerUpdate(BaseModel):
    """Corpo de PUT /api/players/{id}. Editar jogador é editar o apelido."""

    nickname: str = Field(min_length=1, max_length=40)


class PlayerStatusUpdate(BaseModel):
    """Corpo de PATCH /api/players/{id}/status.

    Inativar não apaga nada: o jogador continua no histórico, nos rankings e
    com perfil próprio. Só sai da seleção padrão de uma nova partida.
    """

    status: PlayerStatus
