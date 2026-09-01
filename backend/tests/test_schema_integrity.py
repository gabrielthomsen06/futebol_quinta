"""Regras de integridade garantidas pelo próprio banco.

O que está aqui não depende de nenhuma camada da aplicação lembrar de validar:
são constraints. Mesmo um script rodando SQL na mão esbarra nelas.
"""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus
from app.models.match import Match
from app.models.participation import MatchParticipation
from tests.conftest import criar_jogador, criar_partida


def test_jogador_nao_participa_duas_vezes_da_mesma_partida(session: Session) -> None:
    """Requisito 2 — UNIQUE (match_id, player_id)."""
    gabriel = criar_jogador(session, "Gabriel")
    partida = criar_partida(session, escalacao=[(gabriel, 1, 2, 1)])

    session.add(
        MatchParticipation(
            match_id=partida.id, player_id=gabriel.id, team=1, goals=0, assists=0
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_jogador_nao_pode_estar_nos_dois_times(session: Session) -> None:
    """Requisito 3 — cai no mesmo UNIQUE: seriam duas linhas com o mesmo par."""
    gabriel = criar_jogador(session, "Gabriel")
    partida = criar_partida(session, escalacao=[(gabriel, 1, 0, 0)])

    session.add(
        MatchParticipation(
            match_id=partida.id, player_id=gabriel.id, team=2, goals=0, assists=0
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_gols_nao_podem_ser_negativos(session: Session) -> None:
    """Requisito 4 — CHECK ck_participations_goals."""
    gabriel = criar_jogador(session, "Gabriel")
    with pytest.raises(IntegrityError):
        criar_partida(session, escalacao=[(gabriel, 1, -1, 0)])


def test_assistencias_nao_podem_ser_negativas(session: Session) -> None:
    """Requisito 5 — CHECK ck_participations_assists."""
    gabriel = criar_jogador(session, "Gabriel")
    with pytest.raises(IntegrityError):
        criar_partida(session, escalacao=[(gabriel, 1, 0, -1)])


def test_duas_partidas_podem_ter_a_mesma_data(session: Session) -> None:
    """Requisito 6 — não existe UNIQUE em match_date."""
    data = dt.date(2026, 9, 10)
    primeira = criar_partida(session, data=data, placar=(5, 3))
    segunda = criar_partida(session, data=data, placar=(2, 2))

    session.flush()
    assert primeira.id != segunda.id
    assert primeira.match_date == segunda.match_date


def test_partida_realizada_sem_placar_e_recusada(session: Session) -> None:
    """CHECK ck_matches_played_tem_placar.

    É do placar que saem vitória, empate e derrota de todo mundo — partida
    realizada sem ele não pode existir.
    """
    session.add(
        Match(
            match_date=dt.date(2026, 9, 3),
            status=MatchStatus.PLAYED,
            team_1_name="TIME 1",
            team_2_name="TIME 2",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_partida_agendada_pode_ficar_sem_placar(session: Session) -> None:
    """O mesmo CHECK não pode atrapalhar o fluxo normal de agendar."""
    partida = criar_partida(
        session, status=MatchStatus.SCHEDULED, placar=(None, None)
    )
    session.flush()

    assert partida.team_1_score is None


def test_apagar_jogador_com_historico_e_recusado(session: Session) -> None:
    """ON DELETE RESTRICT — o histórico protege o jogador.

    Quem sai do grupo é inativado, nunca apagado.
    """
    gabriel = criar_jogador(session, "Gabriel")
    criar_partida(session, escalacao=[(gabriel, 1, 2, 1)])

    session.delete(gabriel)
    with pytest.raises(IntegrityError):
        session.flush()


def test_apelido_duplicado_ignorando_caixa_e_recusado(session: Session) -> None:
    """Índice único em lower(nickname)."""
    criar_jogador(session, "Gabriel")

    # criar_jogador já faz flush, então a violação estoura aqui dentro.
    with pytest.raises(IntegrityError):
        criar_jogador(session, "gabriel")


def test_players_nao_tem_contadores_agregados(engine: Engine) -> None:
    """Requisito 13 — estatística é derivada, nunca armazenada.

    Este teste é um alarme: se algum dia alguém "otimizar" acrescentando um
    contador na tabela de jogadores, a suíte quebra e a conversa acontece
    antes de o dado poder dessincronizar do histórico.
    """
    colunas = {c["name"] for c in inspect(engine).get_columns("players")}
    proibidas = {"total_goals", "total_assists", "total_matches", "total_wins"}

    assert not (colunas & proibidas)
    assert colunas == {
        "id",
        "nickname",
        "photo_path",
        "status",
        "created_at",
        "updated_at",
    }
