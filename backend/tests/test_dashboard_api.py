"""Painel da tela inicial."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus
from app.services import dashboard_service
from tests.conftest import criar_jogador, criar_partida

ROTA = "/api/dashboard"
TEMPORADA = 2026


def _painel(session: Session, hoje: dt.date = dt.date(2026, 9, 2)):
    """Chama o service com um "hoje" fixo, sem depender do relógio."""
    return dashboard_service.build(session, season=TEMPORADA, today=hoje)


# --------------------------------------------------------------------------
# Vazio e acesso
# --------------------------------------------------------------------------


def test_dashboard_e_publico(api: TestClient) -> None:
    """A tela inicial abre sem login, como todo o resto da leitura."""
    assert api.get(ROTA).status_code == 200


def test_banco_vazio_devolve_zeros(api: TestClient) -> None:
    corpo = api.get(ROTA).json()

    assert corpo["totals"] == {
        "matches_played": 0,
        "goals_registered": 0,
        "assists_registered": 0,
    }
    assert corpo["next_match"] is None
    assert corpo["last_match"] is None
    assert corpo["top_scorers"] == []
    assert corpo["top_assists"] == []
    assert corpo["goals_timeline"] == []


# --------------------------------------------------------------------------
# Totais
# --------------------------------------------------------------------------


def test_totais_contam_so_partidas_realizadas(session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(2, 1),
        escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 1, 0)],
    )
    criar_partida(
        session,
        data=dt.date(2026, 9, 10),
        status=MatchStatus.SCHEDULED,
        placar=(None, None),
        escalacao=[(gabriel, 1, 0, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session,
        data=dt.date(2026, 8, 20),
        status=MatchStatus.CANCELLED,
        placar=(9, 9),
        escalacao=[(gabriel, 1, 7, 7), (carlos, 2, 0, 0)],
    )

    totais = _painel(session).totals

    assert totais.matches_played == 1
    assert totais.goals == 3
    assert totais.assists == 1


def test_gols_registrados_sao_os_individuais_e_nao_o_placar(session: Session) -> None:
    """A regra central do sistema, do ponto de vista do dashboard.

    Placar 6x4 — dez gols oficiais — mas só 4 lançados na folha. O card diz
    "gols registrados" justamente porque mostra os lançados.
    """
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(6, 4),
        escalacao=[(gabriel, 1, 3, 0), (carlos, 2, 1, 0)],
    )

    assert _painel(session).totals.goals == 4


def test_temporada_recorta_os_totais(session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session, data=dt.date(2025, 12, 18), placar=(1, 0),
        escalacao=[(gabriel, 1, 1, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session, data=dt.date(2026, 1, 8), placar=(2, 0),
        escalacao=[(gabriel, 1, 2, 0), (carlos, 2, 0, 0)],
    )

    assert _painel(session).totals.matches_played == 1
    assert _painel(session).totals.goals == 2


# --------------------------------------------------------------------------
# Próxima e última partida
# --------------------------------------------------------------------------


def test_proxima_partida_e_a_agendada_mais_proxima(session: Session) -> None:
    criar_partida(session, data=dt.date(2026, 9, 24), status=MatchStatus.SCHEDULED, placar=(None, None))
    criar_partida(session, data=dt.date(2026, 9, 10), status=MatchStatus.SCHEDULED, placar=(None, None))

    proxima = _painel(session, hoje=dt.date(2026, 9, 2)).next_match

    assert proxima is not None
    assert proxima.match_date == dt.date(2026, 9, 10)


def test_agendada_no_passado_nao_e_a_proxima(session: Session) -> None:
    """Alguém esqueceu de marcar como realizada — isso não pode virar "próxima"."""
    criar_partida(session, data=dt.date(2026, 8, 20), status=MatchStatus.SCHEDULED, placar=(None, None))

    assert _painel(session, hoje=dt.date(2026, 9, 2)).next_match is None


def test_partida_de_hoje_ainda_conta_como_proxima(session: Session) -> None:
    """A pelada é hoje à noite: ela precisa aparecer no card."""
    hoje = dt.date(2026, 9, 3)
    criar_partida(session, data=hoje, status=MatchStatus.SCHEDULED, placar=(None, None))

    proxima = _painel(session, hoje=hoje).next_match

    assert proxima is not None
    assert proxima.match_date == hoje


def test_ultima_partida_e_a_realizada_mais_recente(session: Session) -> None:
    criar_partida(session, data=dt.date(2026, 8, 27), placar=(1, 0))
    criar_partida(session, data=dt.date(2026, 9, 3), placar=(5, 3))
    criar_partida(session, data=dt.date(2026, 9, 17), status=MatchStatus.SCHEDULED, placar=(None, None))

    ultima = _painel(session).last_match

    assert ultima is not None
    assert ultima.match_date == dt.date(2026, 9, 3)


def test_duas_na_mesma_data_a_mais_recente_vence(session: Session) -> None:
    """Com created_at diferente, ganha a criada depois."""
    data = dt.date(2026, 9, 3)
    antiga = criar_partida(session, data=data, placar=(1, 0), team_1_name="PRIMEIRA")
    nova = criar_partida(session, data=data, placar=(2, 0), team_1_name="SEGUNDA")
    # O now() do Postgres e o inicio da transacao, entao dentro de um teste as
    # duas nascem com o mesmo created_at. Aqui separamos explicitamente o que
    # em producao vem de requisicoes diferentes.
    antiga.created_at = dt.datetime(2026, 9, 3, 20, 0, tzinfo=dt.UTC)
    nova.created_at = dt.datetime(2026, 9, 3, 22, 0, tzinfo=dt.UTC)
    session.flush()

    ultima = _painel(session).last_match

    assert ultima is not None
    assert ultima.id == nova.id


def test_ordenacao_e_estavel_mesmo_com_created_at_identico(session: Session) -> None:
    """Empate total nao pode deixar a tela alternando entre duas partidas."""
    data = dt.date(2026, 9, 3)
    criar_partida(session, data=data, placar=(1, 0), team_1_name="PRIMEIRA")
    criar_partida(session, data=data, placar=(2, 0), team_1_name="SEGUNDA")

    primeira_leitura = _painel(session).last_match
    segunda_leitura = _painel(session).last_match

    assert primeira_leitura is not None
    assert primeira_leitura.id == segunda_leitura.id


# --------------------------------------------------------------------------
# Rankings e série do gráfico
# --------------------------------------------------------------------------


def test_top_artilheiros_ordenado_e_limitado(session: Session) -> None:
    jogadores = [criar_jogador(session, f"Jogador {i}") for i in range(7)]
    adversario = criar_jogador(session, "Adversário")
    for indice, jogador in enumerate(jogadores):
        criar_partida(
            session,
            data=dt.date(2026, 9, 1) + dt.timedelta(days=indice),
            placar=(indice + 1, 0),
            escalacao=[(jogador, 1, indice + 1, 0), (adversario, 2, 0, 0)],
        )

    top = _painel(session).top_scorers

    assert len(top) == 5
    assert [e.goals for e in top] == [7, 6, 5, 4, 3]


def test_quem_nao_marcou_fica_fora_da_artilharia(session: Session) -> None:
    """Uma lista chamada ARTILHARIA com alguém de 0 gols é ruído."""
    artilheiro = criar_jogador(session, "Artilheiro")
    zagueiro = criar_jogador(session, "Zagueiro")
    criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(1, 0),
        escalacao=[(artilheiro, 1, 1, 0), (zagueiro, 2, 0, 0)],
    )

    apelidos = {e.nickname for e in _painel(session).top_scorers}

    assert apelidos == {"Artilheiro"}


def test_serie_de_gols_so_tem_partidas_realizadas_em_ordem(session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session, data=dt.date(2026, 9, 10), placar=(3, 0),
        escalacao=[(gabriel, 1, 3, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session, data=dt.date(2026, 9, 3), placar=(2, 0),
        escalacao=[(gabriel, 1, 2, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session, data=dt.date(2026, 9, 17), status=MatchStatus.SCHEDULED, placar=(None, None),
        escalacao=[(gabriel, 1, 0, 0), (carlos, 2, 0, 0)],
    )

    serie = _painel(session).goals_timeline

    assert [(p.match_date, p.goals) for p in serie] == [
        (dt.date(2026, 9, 3), 2),
        (dt.date(2026, 9, 10), 3),
    ]
