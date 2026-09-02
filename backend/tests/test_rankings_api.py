"""Rankings pela API: métricas, recortes de período e temporadas."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus, PlayerStatus
from tests.conftest import criar_jogador, criar_partida

ROTA = "/api/rankings"
TEMPORADAS = "/api/seasons"


def _cenario(session: Session) -> tuple:
    """Duas partidas realizadas em meses e anos diferentes.

    2025-12-18 : Gabriel 1 gol
    2026-08-13 : Gabriel 2 gols · Carlos 1 gol
    """
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session,
        data=dt.date(2025, 12, 18),
        placar=(1, 0),
        escalacao=[(gabriel, 1, 1, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session,
        data=dt.date(2026, 8, 13),
        placar=(2, 1),
        escalacao=[(gabriel, 1, 2, 0), (carlos, 2, 1, 0)],
    )
    session.commit()
    return gabriel, carlos


def _gols(resposta) -> dict[str, int]:
    return {e["player"]["nickname"]: e["player"]["goals"] for e in resposta.json()["entries"]}


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------


def test_ranking_e_publico(api: TestClient) -> None:
    assert api.get(ROTA).status_code == 200


def test_metrica_invalida(api: TestClient) -> None:
    assert api.get(f"{ROTA}?metric=melhor_jogador").status_code == 422


@pytest.mark.parametrize(
    ("metric", "piso"),
    [
        ("goals", 0),
        ("assists", 0),
        ("wins", 0),
        ("games", 0),
        ("goals_per_game", 3),
        ("assists_per_game", 3),
    ],
)
def test_piso_de_tres_jogos_so_nas_medias(api: TestClient, metric: str, piso: int) -> None:
    """A tela mostra o piso que a API informa; não recalcula nada."""
    assert api.get(f"{ROTA}?metric={metric}").json()["min_games"] == piso


def test_limite_respeitado(api: TestClient, session: Session) -> None:
    adversario = criar_jogador(session, "Adversário")
    for i in range(6):
        jogador = criar_jogador(session, f"Jogador {i}")
        criar_partida(
            session,
            data=dt.date(2026, 9, 1) + dt.timedelta(days=i),
            placar=(1, 0),
            escalacao=[(jogador, 1, 1, 0), (adversario, 2, 0, 0)],
        )
    session.commit()

    assert len(api.get(f"{ROTA}?limit=3").json()["entries"]) == 3


def test_ordenacao_deterministica_pela_api(api: TestClient, session: Session) -> None:
    """Métrica ↓, menos jogos ↑, apelido ↑ — a mesma ordem em toda chamada."""
    _cenario(session)

    primeira = [e["player"]["nickname"] for e in api.get(ROTA).json()["entries"]]
    segunda = [e["player"]["nickname"] for e in api.get(ROTA).json()["entries"]]

    assert primeira == segunda == ["Gabriel", "Carlos"]


def test_jogador_inativo_continua_no_ranking(api: TestClient, session: Session) -> None:
    gabriel, _ = _cenario(session)
    gabriel.status = PlayerStatus.INACTIVE
    session.commit()

    assert "Gabriel" in _gols(api.get(ROTA))


# --------------------------------------------------------------------------
# Recortes de período
# --------------------------------------------------------------------------


def test_temporada_recorta_o_ano(api: TestClient, session: Session) -> None:
    _cenario(session)

    assert _gols(api.get(f"{ROTA}?season=2026"))["Gabriel"] == 2
    assert _gols(api.get(f"{ROTA}?season=2025"))["Gabriel"] == 1


def test_mes_recorta_inclusive_o_ultimo_dia(api: TestClient, session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    # Dia 31 de agosto: precisa entrar no recorte de 2026-08.
    criar_partida(
        session, data=dt.date(2026, 8, 31), placar=(3, 0),
        escalacao=[(gabriel, 1, 3, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session, data=dt.date(2026, 9, 1), placar=(1, 0),
        escalacao=[(gabriel, 1, 1, 0), (carlos, 2, 0, 0)],
    )
    session.commit()

    corpo = api.get(f"{ROTA}?month=2026-08").json()

    assert corpo["date_from"] == "2026-08-01"
    assert corpo["date_to"] == "2026-08-31"
    assert corpo["entries"][0]["player"]["goals"] == 3


def test_intervalo_com_as_duas_pontas(api: TestClient, session: Session) -> None:
    _cenario(session)

    corpo = api.get(f"{ROTA}?date_from=2026-01-01&date_to=2026-12-31").json()

    assert corpo["entries"][0]["player"]["goals"] == 2


def test_apenas_date_from(api: TestClient, session: Session) -> None:
    """"De 2026 em diante" é um recorte legítimo."""
    _cenario(session)

    assert _gols(api.get(f"{ROTA}?date_from=2026-01-01"))["Gabriel"] == 2


def test_apenas_date_to(api: TestClient, session: Session) -> None:
    """"Até o fim de 2025" também."""
    _cenario(session)

    assert _gols(api.get(f"{ROTA}?date_to=2025-12-31"))["Gabriel"] == 1


def test_geral_cobre_todo_o_historico(api: TestClient, session: Session) -> None:
    """Sem parâmetro de período, entram as duas temporadas."""
    _cenario(session)

    corpo = api.get(ROTA).json()

    assert corpo["date_from"] is None
    assert corpo["date_to"] is None
    assert _gols(corpo and api.get(ROTA))["Gabriel"] == 3


def test_data_inicial_depois_da_final(api: TestClient) -> None:
    """Intervalo invertido é erro de quem chamou, não filtro vazio."""
    resposta = api.get(f"{ROTA}?date_from=2026-09-01&date_to=2026-08-01")

    assert resposta.status_code == 400
    assert "depois da data final" in resposta.json()["detail"]


@pytest.mark.parametrize("mes", ["2026-13", "2026-00", "2026-8", "08/2026", "agosto"])
def test_mes_malformado(api: TestClient, mes: str) -> None:
    resposta = api.get(f"{ROTA}?month={mes}")

    assert resposta.status_code == 400
    assert "AAAA-MM" in resposta.json()["detail"]


def test_temporada_fora_do_intervalo(api: TestClient) -> None:
    assert api.get(f"{ROTA}?season=1999").status_code == 400


@pytest.mark.parametrize(
    "combinacao",
    [
        "season=2026&month=2026-08",
        "season=2026&date_from=2026-01-01",
        "month=2026-08&date_to=2026-08-31",
    ],
)
def test_recortes_combinados(api: TestClient, combinacao: str) -> None:
    """Precedência silenciosa surpreende; 400 explica."""
    resposta = api.get(f"{ROTA}?{combinacao}")

    assert resposta.status_code == 400
    assert "só um recorte" in resposta.json()["detail"]


# --------------------------------------------------------------------------
# Status das partidas
# --------------------------------------------------------------------------


def test_agendada_e_cancelada_ficam_fora_do_ranking(
    api: TestClient, session: Session
) -> None:
    """Mesmo com gols lançados, elas não pontuam."""
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session, data=dt.date(2026, 9, 3), status=MatchStatus.SCHEDULED, placar=(None, None),
        escalacao=[(gabriel, 1, 5, 0), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session, data=dt.date(2026, 9, 10), status=MatchStatus.CANCELLED, placar=(9, 9),
        escalacao=[(gabriel, 1, 7, 0), (carlos, 2, 0, 0)],
    )
    session.commit()

    # Ninguem tem partida REALIZADA no periodo, entao ninguem e classificado.
    assert api.get(ROTA).json()["entries"] == []


def test_realizada_entra_no_ranking(api: TestClient, session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session, data=dt.date(2026, 9, 3), placar=(4, 0),
        escalacao=[(gabriel, 1, 4, 0), (carlos, 2, 0, 0)],
    )
    session.commit()

    assert _gols(api.get(ROTA))["Gabriel"] == 4


# --------------------------------------------------------------------------
# Temporadas
# --------------------------------------------------------------------------


def test_seasons_conta_qualquer_status(api: TestClient, session: Session) -> None:
    """A pergunta aqui é "que anos existem", não "quem pontuou"."""
    criar_partida(session, data=dt.date(2024, 5, 2), status=MatchStatus.CANCELLED, placar=(0, 0))
    criar_partida(session, data=dt.date(2025, 7, 10), placar=(1, 0))
    criar_partida(
        session, data=dt.date(2026, 9, 24), status=MatchStatus.SCHEDULED, placar=(None, None)
    )
    session.commit()

    corpo = api.get(TEMPORADAS).json()

    assert corpo["available"] == [2026, 2025, 2024]
    assert corpo["current"] == 2026


def test_seasons_em_banco_vazio(api: TestClient) -> None:
    """Sem partidas, a tela ainda precisa saber que ano exibir."""
    corpo = api.get(TEMPORADAS).json()

    assert corpo["available"] == []
    assert corpo["current"] == 2026


# --------------------------------------------------------------------------
# Participação: quem entra no ranking
#
# "Zerado" é quem jogou e não pontuou — esse continua na lista. Quem não jogou
# no período não tem posição.
# --------------------------------------------------------------------------


def test_jogador_sem_jogos_no_periodo_nao_aparece(api: TestClient, session: Session) -> None:
    jogou = criar_jogador(session, "Jogou")
    adversario = criar_jogador(session, "Adversário")
    criar_jogador(session, "Ficou de Fora")
    criar_partida(
        session,
        data=dt.date(2026, 8, 13),
        placar=(1, 0),
        escalacao=[(jogou, 1, 1, 0), (adversario, 2, 0, 0)],
    )
    session.commit()

    apelidos = {e["player"]["nickname"] for e in api.get(f"{ROTA}?season=2026").json()["entries"]}

    assert apelidos == {"Jogou", "Adversário"}
    assert "Ficou de Fora" not in apelidos


def test_jogador_com_jogos_e_zero_na_metrica_continua_aparecendo(
    api: TestClient, session: Session
) -> None:
    """"0 gols em 1 jogo" é informação legítima — o zagueiro fica no ranking."""
    artilheiro = criar_jogador(session, "Artilheiro")
    zagueiro = criar_jogador(session, "Zagueiro")
    criar_partida(
        session,
        data=dt.date(2026, 8, 13),
        placar=(1, 0),
        escalacao=[(artilheiro, 1, 1, 0), (zagueiro, 2, 0, 0)],
    )
    session.commit()

    assert _gols(api.get(f"{ROTA}?season=2026")) == {"Artilheiro": 1, "Zagueiro": 0}


def test_periodo_sem_partidas_devolve_ranking_vazio(api: TestClient, session: Session) -> None:
    """Antes desta regra, um mês sem jogo devolvia o grupo inteiro zerado."""
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session,
        data=dt.date(2026, 8, 13),
        placar=(1, 0),
        escalacao=[(gabriel, 1, 1, 0), (carlos, 2, 0, 0)],
    )
    session.commit()

    assert api.get(f"{ROTA}?month=2026-01").json()["entries"] == []
    assert len(api.get(f"{ROTA}?month=2026-08").json()["entries"]) == 2


def test_piso_de_tres_continua_valendo_nas_medias(api: TestClient, session: Session) -> None:
    """A regra de participação não afrouxa o piso das médias."""
    veterano = criar_jogador(session, "Veterano")
    estreante = criar_jogador(session, "Estreante")
    adversario = criar_jogador(session, "Adversário")
    for dia in (6, 13, 20):
        criar_partida(
            session,
            data=dt.date(2026, 8, dia),
            placar=(1, 0),
            escalacao=[(veterano, 1, 1, 0), (adversario, 2, 0, 0)],
        )
    criar_partida(
        session,
        data=dt.date(2026, 8, 27),
        placar=(3, 0),
        escalacao=[(estreante, 1, 3, 0), (adversario, 2, 0, 0)],
    )
    session.commit()

    simples = {e["player"]["nickname"] for e in api.get(f"{ROTA}?metric=goals").json()["entries"]}
    media = {
        e["player"]["nickname"]
        for e in api.get(f"{ROTA}?metric=goals_per_game").json()["entries"]
    }

    # Com 1 jogo, o estreante é classificado na artilharia...
    assert "Estreante" in simples
    # ...mas não na média, onde o piso de 3 partidas continua valendo.
    assert "Estreante" not in media
    assert {"Veterano", "Adversário"} <= media
