"""Contratos de entrada e saída de partidas."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MatchStatus


class ParticipationRead(BaseModel):
    """Um jogador dentro de uma partida."""

    model_config = ConfigDict(from_attributes=True)

    player_id: uuid.UUID
    nickname: str
    photo_path: str | None
    team: int = Field(ge=1, le=2)
    goals: int
    assists: int


class MatchRead(BaseModel):
    """Partida sem a escalação, para listagens."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_date: dt.date
    status: MatchStatus
    team_1_name: str
    team_2_name: str
    team_1_score: int | None
    team_2_score: int | None
    created_at: dt.datetime
    updated_at: dt.datetime


class MatchDetailRead(MatchRead):
    """Partida com os dois times montados."""

    team_1: list[ParticipationRead]
    team_2: list[ParticipationRead]


class MatchListRead(BaseModel):
    """Listagem paginada."""

    items: list[MatchRead]
    total: int
    limit: int
    offset: int


class ParticipantInput(BaseModel):
    """Um jogador na escalação enviada pelo administrador.

    Gols e assistências são independentes do placar: nenhuma validação aqui
    compara a soma deles com o resultado da partida.
    """

    player_id: uuid.UUID
    team: int = Field(ge=1, le=2)
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)


class MatchWrite(BaseModel):
    """Corpo de criação e edição de partida.

    Consumido pelos endpoints de escrita, que entram com a autenticação da
    Fase 4. O schema existe agora porque o service já é o dono da regra.
    """

    match_date: dt.date
    status: MatchStatus = MatchStatus.SCHEDULED
    team_1_name: str = Field(default="TIME 1", min_length=1, max_length=40)
    team_2_name: str = Field(default="TIME 2", min_length=1, max_length=40)
    team_1_score: int | None = Field(default=None, ge=0)
    team_2_score: int | None = Field(default=None, ge=0)
    participants: list[ParticipantInput] = Field(default_factory=list)
