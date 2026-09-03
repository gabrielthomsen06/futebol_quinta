"""Histórico e detalhes da partida — a leitura pública da Fase 10."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus, PlayerStatus
from tests.conftest import criar_jogador, criar_partida

ROTA = "/api/matches"


def _cenario(session: Session) -> None:
    """Seis partidas cobrindo os três status e duas temporadas."""
    a = criar_jogador(session, "Gabriel")
    b = criar_jogador(session, "Carlos")
    dados = [
        (dt.date(2025, 12, 18), MatchStatus.PLAYED, (1, 0)),
        (dt.date(2026, 8, 6), MatchStatus.PLAYED, (2, 1)),
        (dt.date(2026, 8, 13), MatchStatus.PLAYED, (3, 2)),
        (dt.date(2026, 8, 20), MatchStatus.CANCELLED, (9, 9)),
        (dt.date(2026, 9, 3), MatchStatus.PLAYED, (4, 0)),
        (dt.date(2026, 9, 10), MatchStatus.SCHEDULED, (None, None)),
    ]
    for data, status, placar in dados:
        criar_partida(
            session, data=data, status=status, placar=placar,
            escalacao=[(a, 1, 1, 0), (b, 2, 0, 0)],
        )
    session.commit()


# --------------------------------------------------------------------------
# Listagem
# --------------------------------------------------------------------------


def test_historico_e_publico(api: TestClient) -> None:
    assert api.get(ROTA).status_code == 200


def test_ordenado_do_mais_recente_para_o_mais_antigo(api: TestClient, session: Session) -> None:
    _cenario(session)

    datas = [m["match_date"] for m in api.get(f"{ROTA}?limit=100").json()["items"]]

    assert datas == sorted(datas, reverse=True)


@pytest.mark.parametrize(
    ("status", "esperado"), [("PLAYED", 4), ("SCHEDULED", 1), ("CANCELLED", 1)]
)
def test_filtro_por_status(
    api: TestClient, session: Session, status: str, esperado: int
) -> None:
    _cenario(session)

    corpo = api.get(f"{ROTA}?status={status}&limit=100").json()

    assert corpo["total"] == esperado
    assert all(m["status"] == status for m in corpo["items"])


def test_recorte_por_temporada_e_mes(api: TestClient, session: Session) -> None:
    _cenario(session)

    assert api.get(f"{ROTA}?season=2026").json()["total"] == 5
    assert api.get(f"{ROTA}?season=2025").json()["total"] == 1
    assert api.get(f"{ROTA}?month=2026-08").json()["total"] == 3


def test_recortes_combinados_devolvem_400(api: TestClient) -> None:
    assert api.get(f"{ROTA}?season=2026&month=2026-08").status_code == 400
    assert api.get(f"{ROTA}?date_from=2026-09-01&date_to=2026-08-01").status_code == 400


def test_total_reflete_o_filtro_e_nao_a_pagina(api: TestClient, session: Session) -> None:
    """`total` é quantas partidas o recorte tem, não quantas vieram nesta página."""
    _cenario(session)

    corpo = api.get(f"{ROTA}?limit=2").json()

    assert len(corpo["items"]) == 2
    assert corpo["total"] == 6


def test_paginacao_filtrada_sem_duplicatas_nem_faltantes(
    api: TestClient, session: Session
) -> None:
    """O teste que pega ordenação instável.

    Sem desempate determinístico, a mesma partida apareceria em duas páginas e
    outra sumiria — e o seed, criado numa transação só, tem `created_at`
    idêntico em todas.
    """
    _cenario(session)
    total = api.get(f"{ROTA}?status=PLAYED").json()["total"]

    vistos: list[str] = []
    for offset in range(0, total, 2):
        pagina = api.get(f"{ROTA}?status=PLAYED&limit=2&offset={offset}").json()
        vistos.extend(m["id"] for m in pagina["items"])

    assert len(vistos) == total
    assert len(set(vistos)) == total  # nenhuma repetida
    assert all(
        m["status"] == "PLAYED"
        for m in api.get(f"{ROTA}?status=PLAYED&limit=100").json()["items"]
    )


def test_listagem_correta_sem_o_eager_loading(api: TestClient, session: Session) -> None:
    """Não-regressão: a listagem parou de carregar participações."""
    _cenario(session)

    corpo = api.get(f"{ROTA}?limit=100").json()

    assert corpo["total"] == 6
    # MatchRead não expõe escalação — quem precisa dela chama o detalhe.
    assert "team_1" not in corpo["items"][0]


# --------------------------------------------------------------------------
# Detalhe
# --------------------------------------------------------------------------


def test_detalhe_e_publico_com_times_ordenados(api: TestClient, session: Session) -> None:
    zagueiro = criar_jogador(session, "Zagueiro")
    atacante = criar_jogador(session, "Atacante")
    adversario = criar_jogador(session, "Adversário")
    partida = criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(3, 1),
        escalacao=[(zagueiro, 1, 0, 1), (atacante, 1, 3, 0), (adversario, 2, 1, 0)],
    )
    session.commit()

    corpo = api.get(f"{ROTA}/{partida.id}").json()

    assert [p["nickname"] for p in corpo["team_1"]] == ["Atacante", "Zagueiro"]
    assert corpo["team_1"][0]["goals"] == 3
    assert [p["nickname"] for p in corpo["team_2"]] == ["Adversário"]


def test_detalhe_de_partida_inexistente(api: TestClient) -> None:
    """Link antigo de partida já excluída precisa dar 404, não 500."""
    assert api.get(f"{ROTA}/{uuid.uuid4()}").status_code == 404


def test_agendada_devolve_placar_nulo(api: TestClient, session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    partida = criar_partida(
        session,
        data=dt.date(2026, 9, 10),
        status=MatchStatus.SCHEDULED,
        placar=(None, None),
        escalacao=[(gabriel, 1, 0, 0), (carlos, 2, 0, 0)],
    )
    session.commit()

    corpo = api.get(f"{ROTA}/{partida.id}").json()

    assert corpo["team_1_score"] is None
    # A escalação prevista existe; é a tela que não mostra estatística.
    assert len(corpo["team_1"]) == 1


def test_agendada_sem_escalacao(api: TestClient, session: Session) -> None:
    """"Times ainda não definidos" na tela nasce daqui."""
    partida = criar_partida(
        session, data=dt.date(2026, 9, 10), status=MatchStatus.SCHEDULED, placar=(None, None)
    )
    session.commit()

    corpo = api.get(f"{ROTA}/{partida.id}").json()

    assert corpo["team_1"] == []
    assert corpo["team_2"] == []


def test_cancelada_mantem_o_placar_guardado(api: TestClient, session: Session) -> None:
    """O dado fica no banco; quem não o exibe é a interface."""
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    partida = criar_partida(
        session,
        data=dt.date(2026, 8, 20),
        status=MatchStatus.CANCELLED,
        placar=(5, 3),
        escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 0, 0)],
    )
    session.commit()

    corpo = api.get(f"{ROTA}/{partida.id}").json()

    assert corpo["status"] == "CANCELLED"
    assert corpo["team_1_score"] == 5
    assert corpo["team_1"][0]["goals"] == 2


# --------------------------------------------------------------------------
# Casos que a tela precisa aguentar
# --------------------------------------------------------------------------


def test_partida_com_mais_de_sete_jogadores_por_time(
    api: TestClient, session: Session
) -> None:
    """Não existe limite de jogadores no sistema, e a tela monta os dois times."""
    escalacao = []
    for i in range(9):
        escalacao.append((criar_jogador(session, f"Time1 {i}"), 1, 0, 0))
    for i in range(8):
        escalacao.append((criar_jogador(session, f"Time2 {i}"), 2, 0, 0))
    partida = criar_partida(
        session, data=dt.date(2026, 9, 3), placar=(4, 2), escalacao=escalacao
    )
    session.commit()

    corpo = api.get(f"{ROTA}/{partida.id}").json()

    assert len(corpo["team_1"]) == 9
    assert len(corpo["team_2"]) == 8


def test_participante_hoje_inativo_continua_na_escalacao(
    api: TestClient, session: Session
) -> None:
    """Inativar não reescreve o passado: ele jogou aquela partida."""
    saiu = criar_jogador(session, "Saiu do Grupo")
    ficou = criar_jogador(session, "Ficou")
    partida = criar_partida(
        session,
        data=dt.date(2026, 8, 13),
        placar=(2, 1),
        escalacao=[(saiu, 1, 2, 0), (ficou, 2, 1, 0)],
    )
    session.commit()

    saiu.status = PlayerStatus.INACTIVE
    session.commit()

    corpo = api.get(f"{ROTA}/{partida.id}").json()

    assert [p["nickname"] for p in corpo["team_1"]] == ["Saiu do Grupo"]
    assert corpo["team_1"][0]["goals"] == 2
