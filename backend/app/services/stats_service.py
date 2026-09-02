"""Regras de negócio das estatísticas derivadas.

O repositório devolve os números brutos; aqui saem as médias, o aproveitamento
e a regra do piso de partidas nos rankings de média.
"""

from __future__ import annotations

import calendar
import datetime as dt
import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import (
    AVERAGE_METRICS,
    MIN_GAMES_FOR_AVERAGE,
    PlayerStatus,
    RankingMetric,
)
from app.core.exceptions import DomainError
from app.repositories import stats_repository
from app.repositories.stats_repository import PlayerMatchRow, PlayerStatsRow
from app.services import player_service


@dataclass(frozen=True, slots=True)
class PlayerStats:
    """Estatísticas de um jogador, brutas e derivadas."""

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
    goals_per_game: float
    assists_per_game: float
    win_rate: float
    goal_participations: int


def _derive(row: PlayerStatsRow) -> PlayerStats:
    """Acrescenta o que é calculado, protegendo contra divisão por zero."""
    games = row.games
    return PlayerStats(
        player_id=row.player_id,
        nickname=row.nickname,
        photo_path=row.photo_path,
        status=row.status,
        games=games,
        goals=row.goals,
        assists=row.assists,
        wins=row.wins,
        draws=row.draws,
        losses=row.losses,
        goals_per_game=round(row.goals / games, 2) if games else 0.0,
        assists_per_game=round(row.assists / games, 2) if games else 0.0,
        win_rate=round(row.wins / games * 100, 1) if games else 0.0,
        goal_participations=row.goals + row.assists,
    )


def players_with_stats(
    session: Session,
    *,
    statuses: Sequence[PlayerStatus] | None = None,
    search: str | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[PlayerStats]:
    """Todos os jogadores e suas estatísticas em uma consulta só."""
    rows = stats_repository.player_stats(
        session,
        statuses=statuses,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    return [_derive(row) for row in rows]


def player_stats(
    session: Session,
    player_id: uuid.UUID,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> PlayerStats:
    """Estatísticas de um jogador. Erro 404 se ele não existir."""
    player_service.get_player(session, player_id)
    rows = stats_repository.player_stats(
        session, player_id=player_id, date_from=date_from, date_to=date_to
    )
    return _derive(rows[0])


def player_match_history(
    session: Session,
    player_id: uuid.UUID,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[PlayerMatchRow]:
    return stats_repository.player_match_history(
        session, player_id, date_from=date_from, date_to=date_to
    )


def min_games_for(metric: RankingMetric) -> int:
    """O piso de 3 partidas vale só para os rankings de média.

    Gols, assistências, vitórias e jogos não têm piso: quem jogou uma vez e
    fez 3 gols merece aparecer na artilharia, só não pode liderar a média
    para sempre com 3,00.
    """
    return MIN_GAMES_FOR_AVERAGE if metric in AVERAGE_METRICS else 0


def ranking(
    session: Session,
    metric: RankingMetric,
    *,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int | None = None,
    min_games: int | None = None,
) -> list[PlayerStats]:
    """Ranking ordenado pela métrica, com desempate determinístico.

    Jogadores inativos continuam presentes: eles fizeram aqueles gols, e o
    histórico não muda porque alguém parou de jogar.
    """
    piso = min_games_for(metric) if min_games is None else min_games
    # Um ranking lista quem entrou em campo no periodo. Quem tem 0 partidas nao
    # tem posicao — e sem esse piso um mes sem jogo devolveria o grupo inteiro
    # zerado, em vez do estado vazio. Quem jogou e nao pontuou continua na
    # lista: "0 gols em 8 jogos" e informacao.
    #
    # Reaproveita o min_games que o repositorio ja tem: nenhuma regra nova,
    # nenhuma consulta nova.
    piso = max(piso, 1)
    rows = stats_repository.player_stats(
        session,
        metric=metric,
        min_games=piso,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [_derive(row) for row in rows]


# --------------------------------------------------------------------------
# Recorte de período
#
# Temporada, mês e intervalo livre são três formas de pedir a mesma coisa: um
# par de datas. A tradução acontece **aqui, no servidor** — o frontend manda o
# que o usuário escolheu e não faz aritmética de calendário.
# --------------------------------------------------------------------------

ANO_MINIMO = 2000
ANO_MAXIMO = 2100
_FORMATO_DE_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def resolver_periodo(
    *,
    season: int | None = None,
    month: str | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> tuple[dt.date | None, dt.date | None]:
    """Converte a escolha do usuário num par de datas.

    Os três modos são mutuamente exclusivos. Combinar dois deles é erro de quem
    chamou, e responder com uma precedência silenciosa esconderia o engano —
    então levanta 400.

    Sem nenhum parâmetro, devolve (None, None): é o "Geral", que cobre todo o
    histórico.
    """
    tem_intervalo = date_from is not None or date_to is not None
    modos = sum([season is not None, month is not None, tem_intervalo])
    if modos > 1:
        raise DomainError(
            "Escolha só um recorte: temporada, mês ou intervalo de datas."
        )

    if season is not None:
        if not ANO_MINIMO <= season <= ANO_MAXIMO:
            raise DomainError(
                f"Temporada inválida. Informe um ano entre {ANO_MINIMO} e {ANO_MAXIMO}."
            )
        return dt.date(season, 1, 1), dt.date(season, 12, 31)

    if month is not None:
        if not _FORMATO_DE_MES.match(month):
            raise DomainError("Mês inválido. Use o formato AAAA-MM, por exemplo 2026-08.")
        ano, mes = (int(parte) for parte in month.split("-"))
        if not ANO_MINIMO <= ano <= ANO_MAXIMO:
            raise DomainError(
                f"Mês inválido. O ano precisa estar entre {ANO_MINIMO} e {ANO_MAXIMO}."
            )
        # monthrange devolve (dia da semana do dia 1, quantidade de dias).
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        return dt.date(ano, mes, 1), dt.date(ano, mes, ultimo_dia)

    # Intervalo livre. Cada extremo é opcional: "de agosto em diante" e "até
    # agosto" são recortes legítimos.
    if date_from is not None and date_to is not None and date_from > date_to:
        raise DomainError("A data inicial não pode ser depois da data final.")

    return date_from, date_to
