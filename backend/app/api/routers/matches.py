"""Endpoints de leitura de partidas."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.models.enums import MatchStatus
from app.models.match import Match
from app.schemas.match import (
    MatchDetailRead,
    MatchListRead,
    MatchRead,
    ParticipationRead,
)
from app.services import match_service

router = APIRouter(prefix="/matches", tags=["partidas"])


@router.get("", response_model=MatchListRead, summary="Lista partidas")
def list_matches(
    session: SessionDep,
    status: Annotated[MatchStatus | None, Query(description="Filtra por status")] = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MatchListRead:
    matches, total = match_service.list_matches(
        session,
        statuses=[status] if status else None,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return MatchListRead(
        items=[MatchRead.model_validate(m) for m in matches],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{match_id}", response_model=MatchDetailRead, summary="Detalhe de uma partida"
)
def get_match(session: SessionDep, match_id: uuid.UUID) -> MatchDetailRead:
    match = match_service.get_match(session, match_id)
    return _to_detail(match)


def _to_detail(match: Match) -> MatchDetailRead:
    """Separa a escalação nos dois lados, ordenada por apelido."""

    def lado(numero: int) -> list[ParticipationRead]:
        participacoes = [p for p in match.participations if p.team == numero]
        participacoes.sort(key=lambda p: p.player.nickname.lower())
        return [
            ParticipationRead(
                player_id=p.player_id,
                nickname=p.player.nickname,
                photo_path=p.player.photo_path,
                team=p.team,
                goals=p.goals,
                assists=p.assists,
            )
            for p in participacoes
        ]

    return MatchDetailRead(
        **MatchRead.model_validate(match).model_dump(),
        team_1=lado(1),
        team_2=lado(2),
    )
