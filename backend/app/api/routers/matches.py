"""Endpoints de leitura de partidas."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminDep, SessionDep
from app.models.enums import MatchStatus
from app.models.match import Match
from app.schemas.match import (
    MatchDetailRead,
    MatchListRead,
    MatchRead,
    MatchWrite,
    ParticipationRead,
)
from app.services import match_service, stats_service
from app.services.match_service import ParticipantInput

router = APIRouter(prefix="/matches", tags=["partidas"])


@router.get(
    "",
    response_model=MatchListRead,
    summary="Lista partidas",
    responses={400: {"description": "Recorte de período inválido ou combinado"}},
)
def list_matches(
    session: SessionDep,
    status_filtro: Annotated[
        MatchStatus | None, Query(alias="status", description="Filtra por status")
    ] = None,
    season: Annotated[
        int | None,
        Query(description="Ano inteiro. Exclusivo com month e com o intervalo de datas."),
    ] = None,
    month: Annotated[
        str | None,
        Query(description="AAAA-MM. Exclusivo com season e com o intervalo de datas."),
    ] = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MatchListRead:
    # Mesma função que os rankings usam desde a Fase 9: temporada, mês e
    # intervalo viram um par de datas no servidor, com as mesmas mensagens de
    # erro. Nada de reimplementar aritmética de calendário.
    inicio, fim = stats_service.resolver_periodo(
        season=season, month=month, date_from=date_from, date_to=date_to
    )

    matches, total = match_service.list_matches(
        session,
        statuses=[status_filtro] if status_filtro else None,
        date_from=inicio,
        date_to=fim,
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


# --------------------------------------------------------------------------
# Escrita — exige o administrador.
#
# Nenhuma regra nova mora aqui: a validação inteira (jogador repetido, time
# fora de 1-2, REALIZADA exigindo placar e os dois times) já vive em
# match_service._validate desde a Fase 3. O router só traduz HTTP.
# --------------------------------------------------------------------------


def _participantes(dados: MatchWrite) -> list[ParticipantInput]:
    """Converte o corpo validado pelo Pydantic no tipo que o service espera."""
    return [
        ParticipantInput(
            player_id=p.player_id, team=p.team, goals=p.goals, assists=p.assists
        )
        for p in dados.participants
    ]


@router.post(
    "",
    response_model=MatchDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma partida",
    responses={400: {"description": "Escalação ou placar inconsistentes com o status"}},
)
def create_match(dados: MatchWrite, session: SessionDep, admin: AdminDep) -> MatchDetailRead:
    match = match_service.create_match(
        session,
        match_date=dados.match_date,
        status=dados.status,
        team_1_name=dados.team_1_name,
        team_2_name=dados.team_2_name,
        team_1_score=dados.team_1_score,
        team_2_score=dados.team_2_score,
        participants=_participantes(dados),
    )
    return _to_detail(match)


@router.put(
    "/{match_id}",
    response_model=MatchDetailRead,
    summary="Substitui a partida, escalação inclusa",
    responses={400: {"description": "Escalação ou placar inconsistentes com o status"}},
)
def replace_match(
    match_id: uuid.UUID, dados: MatchWrite, session: SessionDep, admin: AdminDep
) -> MatchDetailRead:
    match = match_service.replace_match(
        session,
        match_id,
        match_date=dados.match_date,
        status=dados.status,
        team_1_name=dados.team_1_name,
        team_2_name=dados.team_2_name,
        team_1_score=dados.team_1_score,
        team_2_score=dados.team_2_score,
        participants=_participantes(dados),
    )
    return _to_detail(match)


@router.delete(
    "/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui a partida e as estatísticas dela",
)
def delete_match(match_id: uuid.UUID, session: SessionDep, admin: AdminDep) -> None:
    match_service.delete_match(session, match_id)
