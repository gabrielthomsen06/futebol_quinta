"""Dados fictícios de desenvolvimento.

**Isto não é dado real.** Os apelidos são de exemplo e as partidas foram
inventadas para dar o que olhar nas telas enquanto o sistema é construído.
Nunca rode em produção.

Chamado por `python -m app.cli seed`.
"""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import MatchStatus, PlayerStatus
from app.models.match import Match
from app.services import match_service, player_service
from app.services.match_service import ParticipantInput

logger = logging.getLogger(__name__)

APELIDOS = [
    "Gabriel",
    "João",
    "Pedro",
    "Carlos",
    "Lucas",
    "Rafa",
    "Tiago",
    "Bruno",
    "Diego",
    "Vitor",
]

# Quem saiu do grupo: entra inativo, para a tela de jogadores ter os dois casos.
INATIVOS = {"Vitor"}

# (dias atrás, status, nome do time 1, nome do time 2, placar,
#  gols/assistências do time 1, gols/assistências do time 2)
#
# Repare na partida de 21 dias atrás: placar 6x4 com apenas 4 gols lançados no
# time 1. É proposital — placar e gols individuais são independentes.
PARTIDAS = [
    (28, MatchStatus.PLAYED, "TIME 1", "BRANCO", (5, 3),
     [(0, 2, 1), (1, 1, 2), (2, 1, 0), (3, 0, 1)],
     [(4, 2, 0), (5, 1, 1), (6, 0, 0), (7, 0, 1)]),
    (21, MatchStatus.PLAYED, "AZUL", "PRETO", (6, 4),
     [(0, 2, 1), (2, 1, 1), (4, 1, 0), (6, 0, 2)],
     [(1, 3, 0), (3, 1, 1), (5, 0, 0), (8, 0, 1)]),
    (14, MatchStatus.PLAYED, "TIME 1", "TIME 2", (2, 2),
     [(0, 1, 0), (1, 1, 1), (3, 0, 0), (5, 0, 1)],
     [(2, 1, 1), (4, 1, 0), (7, 0, 0), (9, 0, 0)]),
    (7, MatchStatus.PLAYED, "LARANJA", "BRANCO", (1, 4),
     [(1, 1, 0), (4, 0, 1), (6, 0, 0), (8, 0, 0)],
     [(0, 2, 1), (2, 1, 0), (3, 1, 1), (9, 0, 1)]),
    (3, MatchStatus.CANCELLED, "TIME 1", "TIME 2", (None, None),
     [(0, 0, 0), (1, 0, 0)],
     [(2, 0, 0), (3, 0, 0)]),
    (-4, MatchStatus.SCHEDULED, "TIME 1", "TIME 2", (None, None),
     [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],
     [(4, 0, 0), (5, 0, 0), (6, 0, 0), (7, 0, 0)]),
]


def ja_populado(session: Session) -> bool:
    return (session.scalar(select(func.count()).select_from(Match)) or 0) > 0


def seed(session: Session) -> str:
    """Popula o banco com jogadores e partidas de exemplo.

    Recusa rodar se já existir partida: o objetivo é dar um ponto de partida
    num banco vazio, nunca misturar exemplo com dado de verdade.
    """
    if settings.is_production:
        raise RuntimeError(
            "O seed cria jogadores e partidas ficticios e nao roda em producao. "
            "Se voce quer mesmo popular este banco, faca isso pela interface."
        )

    if ja_populado(session):
        raise RuntimeError(
            "O banco já tem partidas. O seed só roda em base vazia, para não "
            "misturar dados fictícios com os seus."
        )

    jogadores = []
    for apelido in APELIDOS:
        status = PlayerStatus.INACTIVE if apelido in INATIVOS else PlayerStatus.ACTIVE
        jogadores.append(player_service.create_player(session, nickname=apelido, status=status))

    hoje = dt.date.today()
    for dias, status, time_1, time_2, placar, escalacao_1, escalacao_2 in PARTIDAS:
        participantes = [
            ParticipantInput(player_id=jogadores[i].id, team=1, goals=g, assists=a)
            for i, g, a in escalacao_1
        ] + [
            ParticipantInput(player_id=jogadores[i].id, team=2, goals=g, assists=a)
            for i, g, a in escalacao_2
        ]
        match_service.create_match(
            session,
            match_date=hoje - dt.timedelta(days=dias),
            status=status,
            team_1_name=time_1,
            team_2_name=time_2,
            team_1_score=placar[0],
            team_2_score=placar[1],
            participants=participantes,
        )

    return f"{len(APELIDOS)} jogadores e {len(PARTIDAS)} partidas de exemplo."
