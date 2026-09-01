"""Regras de negócio de partidas.

Aqui mora a regra mais importante do sistema — e uma que precisa ser lida como
ausência: **não existe validação alguma comparando a soma dos gols individuais
com o placar da partida**. Placar 5 com 2+1+0 anotados é registro válido. O
placar é o resultado oficial; os gols são anotados na folha durante o jogo e
são independentes.
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, NotFoundError
from app.db.session import transaction
from app.models.enums import MatchStatus
from app.models.match import Match
from app.models.participation import MatchParticipation
from app.repositories import match_repository, player_repository


@dataclass(frozen=True, slots=True)
class ParticipantInput:
    player_id: uuid.UUID
    team: int
    goals: int = 0
    assists: int = 0


def list_matches(
    session: Session,
    *,
    statuses: Sequence[MatchStatus] | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Match], int]:
    matches = match_repository.list_matches(
        session,
        statuses=statuses,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    total = match_repository.count_matches(
        session, statuses=statuses, date_from=date_from, date_to=date_to
    )
    return matches, total


def get_match(session: Session, match_id: uuid.UUID) -> Match:
    match = match_repository.get_match(session, match_id)
    if match is None:
        raise NotFoundError("Partida não encontrada.")
    return match


def create_match(
    session: Session,
    *,
    match_date: dt.date,
    status: MatchStatus,
    team_1_name: str,
    team_2_name: str,
    team_1_score: int | None,
    team_2_score: int | None,
    participants: Sequence[ParticipantInput],
) -> Match:
    """Cria partida e escalação numa transação só."""
    _validate(session, status, team_1_score, team_2_score, participants)

    match = Match(
        match_date=match_date,
        status=status,
        team_1_name=team_1_name.strip(),
        team_2_name=team_2_name.strip(),
        team_1_score=team_1_score,
        team_2_score=team_2_score,
    )
    for p in participants:
        match.participations.append(
            MatchParticipation(
                player_id=p.player_id, team=p.team, goals=p.goals, assists=p.assists
            )
        )

    with transaction(session):
        match_repository.add(session, match)
    return get_match(session, match.id)


def replace_match(
    session: Session,
    match_id: uuid.UUID,
    *,
    match_date: dt.date,
    status: MatchStatus,
    team_1_name: str,
    team_2_name: str,
    team_1_score: int | None,
    team_2_score: int | None,
    participants: Sequence[ParticipantInput],
) -> Match:
    """Substitui a partida inteira, escalação inclusa, numa transação só.

    Reescrever o conjunto é mais simples e mais seguro que reconciliar
    diferenças em ~14 linhas. Como a estatística é derivada, o novo estado
    já vale para rankings e dashboard na leitura seguinte.
    """
    match = get_match(session, match_id)
    _validate(session, status, team_1_score, team_2_score, participants)

    with transaction(session):
        match.match_date = match_date
        match.status = status
        match.team_1_name = team_1_name.strip()
        match.team_2_name = team_2_name.strip()
        match.team_1_score = team_1_score
        match.team_2_score = team_2_score

        match_repository.clear_participations(session, match.id)
        session.expire(match, ["participations"])
        for p in participants:
            session.add(
                MatchParticipation(
                    match_id=match.id,
                    player_id=p.player_id,
                    team=p.team,
                    goals=p.goals,
                    assists=p.assists,
                )
            )

    return get_match(session, match_id)


def delete_match(session: Session, match_id: uuid.UUID) -> None:
    """Exclui a partida; o CASCADE elimina as estatísticas dela junto."""
    match = get_match(session, match_id)
    with transaction(session):
        match_repository.delete_match(session, match)


def _validate(
    session: Session,
    status: MatchStatus,
    team_1_score: int | None,
    team_2_score: int | None,
    participants: Sequence[ParticipantInput],
) -> None:
    """Valida antes de tocar o banco, para o erro sair como mensagem.

    NÃO valida a soma dos gols individuais contra o placar — de propósito.
    """
    vistos: set[uuid.UUID] = set()
    for p in participants:
        if p.team not in (1, 2):
            raise DomainError("O time de um jogador só pode ser 1 ou 2.")
        if p.goals < 0 or p.assists < 0:
            raise DomainError("Gols e assistências não podem ser negativos.")
        if p.player_id in vistos:
            raise DomainError(
                "Um jogador não pode aparecer duas vezes na mesma partida."
            )
        vistos.add(p.player_id)

    if vistos:
        encontrados = {
            player.id
            for player in player_repository.list_players(session)
            if player.id in vistos
        }
        faltando = vistos - encontrados
        if faltando:
            raise NotFoundError("Um dos jogadores selecionados não existe.")

    if status is MatchStatus.PLAYED:
        if team_1_score is None or team_2_score is None:
            raise DomainError(
                "Partida realizada precisa do placar dos dois times."
            )
        times = {p.team for p in participants}
        if times != {1, 2}:
            raise DomainError(
                "Partida realizada precisa de pelo menos um jogador em cada time."
            )
