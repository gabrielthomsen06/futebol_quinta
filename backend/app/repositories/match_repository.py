"""Acesso a dados de partidas. Sem regra de negócio e sem commit."""

from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import MatchStatus
from app.models.match import Match
from app.models.participation import MatchParticipation


def _with_participants() -> tuple:
    """Carrega participações e jogadores junto, evitando N+1.

    São duas consultas no total, independentemente de quantas partidas a
    listagem devolver — nunca uma por partida.
    """
    return (
        selectinload(Match.participations).joinedload(MatchParticipation.player),
    )


def list_matches(
    session: Session,
    *,
    statuses: Sequence[MatchStatus] | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Match]:
    """Partidas da mais recente para a mais antiga.

    Como duas partidas podem dividir a mesma data, created_at desempata para
    a ordenação ser determinística.
    """
    # Sem eager loading: a listagem serializa MatchRead, que nao tem
    # participacoes. Carrega-las seria buscar dezenas de linhas por pagina
    # para descarta-las na serializacao. get_match() mantem o carregamento.
    stmt = select(Match)
    stmt = _apply_filters(stmt, statuses, date_from, date_to)
    # O id desempata: sem ele, partidas com a mesma data e o mesmo created_at
    # (as do seed, criadas numa transacao so) teriam ordem indefinida e a
    # paginacao repetiria ou puliria registros entre as paginas.
    stmt = stmt.order_by(
        Match.match_date.desc(), Match.created_at.desc(), Match.id.desc()
    )
    stmt = stmt.limit(limit).offset(offset)
    return list(session.scalars(stmt).unique())


def count_matches(
    session: Session,
    *,
    statuses: Sequence[MatchStatus] | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> int:
    stmt = select(func.count()).select_from(Match)
    stmt = _apply_filters(stmt, statuses, date_from, date_to)
    return session.scalar(stmt) or 0


def _apply_filters(stmt, statuses, date_from, date_to):  # type: ignore[no-untyped-def]
    if statuses:
        stmt = stmt.where(Match.status.in_(list(statuses)))
    if date_from is not None:
        stmt = stmt.where(Match.match_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Match.match_date <= date_to)
    return stmt


def get_match(session: Session, match_id: uuid.UUID) -> Match | None:
    stmt = (
        select(Match).options(*_with_participants()).where(Match.id == match_id)
    )
    return session.scalars(stmt).unique().first()


def add(session: Session, match: Match) -> Match:
    session.add(match)
    session.flush()
    return match


def delete_match(session: Session, match: Match) -> None:
    """Remove a partida. O ON DELETE CASCADE leva as participações junto."""
    session.delete(match)
    session.flush()


def clear_participations(session: Session, match_id: uuid.UUID) -> None:
    """Apaga a escalação inteira, para ser substituída pela nova.

    Reescrever o conjunto é mais simples e mais seguro que reconciliar
    diferenças em ~14 linhas, e não deixa estado intermediário inválido.
    """
    session.execute(
        delete(MatchParticipation).where(MatchParticipation.match_id == match_id)
    )
    session.flush()


def next_scheduled(session: Session, *, from_date: dt.date) -> Match | None:
    """A partida agendada mais próxima, a partir da data informada.

    `from_date` chega como parâmetro em vez de usar CURRENT_DATE no SQL: assim
    os testes fixam "hoje" em vez de depender do relógio, e a comparação fica
    entre duas datas puras — `match_date` é DATE, sem hora, então não existe a
    virada de dia por fuso horário.

    Uma partida agendada que ficou no passado não é "a próxima": ela some deste
    card e continua no histórico.
    """
    stmt = (
        select(Match)
        .where(Match.status == MatchStatus.SCHEDULED, Match.match_date >= from_date)
        .order_by(Match.match_date.asc(), Match.created_at.asc(), Match.id.asc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def last_played(session: Session) -> Match | None:
    """A partida realizada mais recente.

    Duas partidas podem dividir a mesma data. `created_at` desempata quando elas
    vieram de requisicoes diferentes — que e o caso real. Dentro de uma mesma
    transacao o `now()` do Postgres e identico para as duas, entao o `id` entra
    como criterio final: a ordem nunca fica indefinida, e a tela inicial nao
    alterna entre as duas a cada carregamento.
    """
    stmt = (
        select(Match)
        .where(Match.status == MatchStatus.PLAYED)
        .order_by(Match.match_date.desc(), Match.created_at.desc(), Match.id.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()
