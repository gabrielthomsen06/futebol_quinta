"""Consultas agregadas de estatísticas.

Único lugar do projeto que monta consulta analítica. Nada aqui é armazenado:
jogos, vitórias, gols e assistências saem sempre das partidas REALIZADAS, o que
mantém rankings e perfis coerentes com o histórico logo após qualquer edição
ou exclusão de partida, sem rotina de recálculo.

As consultas são montadas com o Core do SQLAlchemy, não com text(): o ORDER BY
varia conforme a métrica pedida na URL e não aceita parâmetro vinculado —
concatenar string seria abrir porta para injeção. Aqui a métrica chega como
enum e é traduzida por um dicionário fechado de expressões.
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Numeric, and_, case, cast, func, literal, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models.enums import MatchStatus, PlayerStatus, RankingMetric
from app.models.match import Match
from app.models.participation import MatchParticipation
from app.models.player import Player

# Rótulos do resultado dentro da consulta.
_VITORIA = "V"
_EMPATE = "E"
_DERROTA = "D"


@dataclass(frozen=True, slots=True)
class PlayerStatsRow:
    """Linha bruta do agregado. As médias são derivadas no service."""

    player_id: uuid.UUID
    nickname: str
    photo_path: str | None
    status: PlayerStatus
    games: int
    goals: int
    assists: int
    wins: int
    draws: int
    losses: int


@dataclass(frozen=True, slots=True)
class PlayerMatchRow:
    """Uma partida no histórico individual do jogador."""

    match_id: uuid.UUID
    match_date: dt.date
    team_1_name: str
    team_2_name: str
    team_1_score: int
    team_2_score: int
    team: int
    goals: int
    assists: int
    result: str


def _played_cte(date_from: dt.date | None, date_to: dt.date | None):  # type: ignore[no-untyped-def]
    """Participações em partidas realizadas, já com o resultado de cada uma.

    Agendadas e canceladas ficam de fora aqui, na origem — assim nenhuma
    consulta acima precisa lembrar de filtrar por status.
    """
    venceu = or_(
        and_(MatchParticipation.team == 1, Match.team_1_score > Match.team_2_score),
        and_(MatchParticipation.team == 2, Match.team_2_score > Match.team_1_score),
    )
    resultado = case(
        (Match.team_1_score == Match.team_2_score, literal(_EMPATE)),
        (venceu, literal(_VITORIA)),
        else_=literal(_DERROTA),
    )

    stmt = (
        select(
            MatchParticipation.player_id.label("player_id"),
            MatchParticipation.goals.label("goals"),
            MatchParticipation.assists.label("assists"),
            resultado.label("resultado"),
        )
        .join(Match, Match.id == MatchParticipation.match_id)
        .where(Match.status == MatchStatus.PLAYED)
    )
    if date_from is not None:
        stmt = stmt.where(Match.match_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Match.match_date <= date_to)
    return stmt.cte("realizadas")


def player_stats(
    session: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    player_id: uuid.UUID | None = None,
    statuses: Sequence[PlayerStatus] | None = None,
    search: str | None = None,
    min_games: int = 0,
    metric: RankingMetric | None = None,
    limit: int | None = None,
) -> list[PlayerStatsRow]:
    """Agregado de todos os jogadores em uma única consulta.

    O LEFT JOIN garante que quem nunca jogou apareça com tudo zerado, em vez
    de sumir da lista.
    """
    played = _played_cte(date_from, date_to)

    games = func.count(played.c.player_id)
    goals = func.coalesce(func.sum(played.c.goals), 0)
    assists = func.coalesce(func.sum(played.c.assists), 0)
    wins = func.count().filter(played.c.resultado == _VITORIA)
    draws = func.count().filter(played.c.resultado == _EMPATE)
    losses = func.count().filter(played.c.resultado == _DERROTA)

    stmt: Select = (
        select(
            Player.id,
            Player.nickname,
            Player.photo_path,
            Player.status,
            games.label("games"),
            goals.label("goals"),
            assists.label("assists"),
            wins.label("wins"),
            draws.label("draws"),
            losses.label("losses"),
        )
        .select_from(Player)
        .outerjoin(played, played.c.player_id == Player.id)
        .group_by(Player.id)
    )

    if player_id is not None:
        stmt = stmt.where(Player.id == player_id)
    if statuses:
        stmt = stmt.where(Player.status.in_(list(statuses)))
    if search:
        stmt = stmt.where(Player.nickname.ilike(f"%{search.strip()}%"))
    if min_games > 0:
        stmt = stmt.having(games >= min_games)

    stmt = stmt.order_by(*_order_by(metric, games, goals, assists, wins))
    if limit is not None:
        stmt = stmt.limit(limit)

    return [
        PlayerStatsRow(
            player_id=row.id,
            nickname=row.nickname,
            photo_path=row.photo_path,
            status=row.status,
            games=row.games,
            goals=row.goals,
            assists=row.assists,
            wins=row.wins,
            draws=row.draws,
            losses=row.losses,
        )
        for row in session.execute(stmt)
    ]


def _order_by(  # type: ignore[no-untyped-def]
    metric: RankingMetric | None, games, goals, assists, wins
):
    """Ordenação determinística: métrica DESC, menos jogos, apelido.

    Sem o desempate explícito, dois jogadores empatados trocariam de posição
    entre requisições — o que quebraria a leitura da tela e os testes.
    """
    if metric is None:
        return (Player.nickname.asc(),)

    # Média calculada no banco só para ordenar; a exibida é formatada
    # em Python, no service.
    per_game = lambda total: func.coalesce(  # noqa: E731
        cast(total, Numeric) / func.nullif(games, 0), 0
    )

    expressions = {
        RankingMetric.GOALS: goals,
        RankingMetric.ASSISTS: assists,
        RankingMetric.WINS: wins,
        RankingMetric.GAMES: games,
        RankingMetric.GOALS_PER_GAME: per_game(goals),
        RankingMetric.ASSISTS_PER_GAME: per_game(assists),
    }
    return (expressions[metric].desc(), games.asc(), Player.nickname.asc())


def player_match_history(
    session: Session,
    player_id: uuid.UUID,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[PlayerMatchRow]:
    """Partidas realizadas de um jogador, da mais recente para a mais antiga."""
    venceu = or_(
        and_(MatchParticipation.team == 1, Match.team_1_score > Match.team_2_score),
        and_(MatchParticipation.team == 2, Match.team_2_score > Match.team_1_score),
    )
    resultado = case(
        (Match.team_1_score == Match.team_2_score, literal(_EMPATE)),
        (venceu, literal(_VITORIA)),
        else_=literal(_DERROTA),
    )

    stmt = (
        select(
            Match.id,
            Match.match_date,
            Match.team_1_name,
            Match.team_2_name,
            Match.team_1_score,
            Match.team_2_score,
            MatchParticipation.team,
            MatchParticipation.goals,
            MatchParticipation.assists,
            resultado.label("resultado"),
        )
        .join(MatchParticipation, MatchParticipation.match_id == Match.id)
        .where(
            MatchParticipation.player_id == player_id,
            Match.status == MatchStatus.PLAYED,
        )
        .order_by(Match.match_date.desc(), Match.created_at.desc())
    )
    if date_from is not None:
        stmt = stmt.where(Match.match_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Match.match_date <= date_to)

    return [
        PlayerMatchRow(
            match_id=row.id,
            match_date=row.match_date,
            team_1_name=row.team_1_name,
            team_2_name=row.team_2_name,
            team_1_score=row.team_1_score,
            team_2_score=row.team_2_score,
            team=row.team,
            goals=row.goals,
            assists=row.assists,
            result=row.resultado,
        )
        for row in session.execute(stmt)
    ]


@dataclass(frozen=True, slots=True)
class SeasonTotals:
    """Os três números grandes da tela inicial."""

    matches_played: int
    goals: int
    assists: int


@dataclass(frozen=True, slots=True)
class GoalsPoint:
    """Um ponto da série temporal de gols."""

    match_date: dt.date
    goals: int


def _no_periodo(stmt, date_from: dt.date | None, date_to: dt.date | None):  # type: ignore[no-untyped-def]
    if date_from is not None:
        stmt = stmt.where(Match.match_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Match.match_date <= date_to)
    return stmt


def season_totals(
    session: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> SeasonTotals:
    """Totais do período, contando apenas partidas realizadas.

    Gols e assistências são a **soma dos lançamentos individuais**, não dos
    placares. Os dois números são independentes por definição, e o rótulo da
    tela diz "gols registrados" justamente por isso.
    """
    partidas = select(func.count()).select_from(Match).where(Match.status == MatchStatus.PLAYED)
    total_de_partidas = session.scalar(_no_periodo(partidas, date_from, date_to)) or 0

    agregados = (
        select(
            func.coalesce(func.sum(MatchParticipation.goals), 0),
            func.coalesce(func.sum(MatchParticipation.assists), 0),
        )
        .select_from(MatchParticipation)
        .join(Match, Match.id == MatchParticipation.match_id)
        .where(Match.status == MatchStatus.PLAYED)
    )
    gols, assistencias = session.execute(_no_periodo(agregados, date_from, date_to)).one()

    return SeasonTotals(matches_played=total_de_partidas, goals=gols, assists=assistencias)


def goals_timeline(
    session: Session,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[GoalsPoint]:
    """Gols registrados por data, em ordem crescente.

    Agrupa por **data** e não por partida: nas raras quintas com dois jogos, os
    dois viram um ponto só — que é o certo para um eixo temporal.

    O LEFT JOIN mantém no gráfico uma partida realizada em que ninguém anotou
    gol: ela aparece como zero, em vez de sumir da linha.
    """
    stmt = (
        select(
            Match.match_date,
            func.coalesce(func.sum(MatchParticipation.goals), 0).label("goals"),
        )
        .select_from(Match)
        .outerjoin(MatchParticipation, MatchParticipation.match_id == Match.id)
        .where(Match.status == MatchStatus.PLAYED)
        .group_by(Match.match_date)
        .order_by(Match.match_date.asc())
    )
    return [
        GoalsPoint(match_date=linha.match_date, goals=linha.goals)
        for linha in session.execute(_no_periodo(stmt, date_from, date_to))
    ]
