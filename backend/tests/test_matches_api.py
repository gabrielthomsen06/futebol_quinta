"""Partidas pela API: escrita autenticada, validação e efeito nas estatísticas.

A camada de serviço já está coberta desde a Fase 3. O que se prova aqui é o
contrato HTTP e o que acontece com as estatísticas depois de editar e excluir.
"""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import stats_service
from tests.conftest import criar_jogador

ROTA = "/api/matches"


def _corpo(
    jogadores: list,
    *,
    status: str = "PLAYED",
    placar: tuple[int | None, int | None] = (5, 3),
    data: str = "2026-09-03",
    gols: dict[int, int] | None = None,
) -> dict:
    """Monta o corpo com os dois primeiros jogadores no time 1 e o resto no 2."""
    gols = gols or {}
    participantes = []
    for indice, jogador in enumerate(jogadores):
        participantes.append(
            {
                "player_id": str(jogador.id),
                "team": 1 if indice < 2 else 2,
                "goals": gols.get(indice, 0),
                "assists": 0,
            }
        )
    return {
        "match_date": data,
        "status": status,
        "team_1_name": "TIME 1",
        "team_2_name": "BRANCO",
        "team_1_score": placar[0],
        "team_2_score": placar[1],
        "participants": participantes,
    }


def _quatro_jogadores(session: Session) -> list:
    jogadores = [criar_jogador(session, nome) for nome in ("Gabriel", "João", "Carlos", "Lucas")]
    session.commit()
    return jogadores


# --------------------------------------------------------------------------
# Criar
# --------------------------------------------------------------------------


def test_cria_partida_com_escalacao(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)

    resposta = api.post(ROTA, json=_corpo(jogadores, gols={0: 2, 1: 1}), headers=auth_headers)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "PLAYED"
    assert corpo["team_2_name"] == "BRANCO"
    assert [p["nickname"] for p in corpo["team_1"]] == ["Gabriel", "João"]
    assert [p["nickname"] for p in corpo["team_2"]] == ["Carlos", "Lucas"]


def test_cria_sem_token(api: TestClient, session: Session) -> None:
    jogadores = _quatro_jogadores(session)

    assert api.post(ROTA, json=_corpo(jogadores)).status_code == 401


def test_gols_individuais_nao_precisam_bater_com_o_placar(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    """A regra mais importante do sistema, verificada pela API.

    Placar 6x4 com apenas 4 gols lançados é registro válido: o placar é o
    resultado oficial e os gols vêm da folha anotada durante o jogo.
    """
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores, placar=(6, 4), gols={0: 2, 1: 1, 2: 1})

    resposta = api.post(ROTA, json=corpo, headers=auth_headers)

    assert resposta.status_code == 201
    assert resposta.json()["team_1_score"] == 6
    # O agregado segue os gols individuais, não o placar.
    assert stats_service.player_stats(session, jogadores[0].id).goals == 2


def test_duas_partidas_na_mesma_data(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)

    primeira = api.post(ROTA, json=_corpo(jogadores, data="2026-09-10"), headers=auth_headers)
    segunda = api.post(ROTA, json=_corpo(jogadores, data="2026-09-10"), headers=auth_headers)

    assert primeira.status_code == segunda.status_code == 201
    assert primeira.json()["id"] != segunda.json()["id"]


# --------------------------------------------------------------------------
# Validação pela API
# --------------------------------------------------------------------------


def test_realizada_sem_placar(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores, placar=(None, None))

    resposta = api.post(ROTA, json=corpo, headers=auth_headers)

    assert resposta.status_code == 400
    assert "placar" in resposta.json()["detail"]


def test_realizada_com_um_time_so(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores)
    for participante in corpo["participants"]:
        participante["team"] = 1

    resposta = api.post(ROTA, json=corpo, headers=auth_headers)

    assert resposta.status_code == 400
    assert "cada time" in resposta.json()["detail"]


def test_jogador_repetido(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores)
    corpo["participants"][2]["player_id"] = corpo["participants"][0]["player_id"]

    resposta = api.post(ROTA, json=corpo, headers=auth_headers)

    assert resposta.status_code == 400
    assert "duas vezes" in resposta.json()["detail"]


def test_jogador_inexistente(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores)
    corpo["participants"][0]["player_id"] = str(uuid.uuid4())

    assert api.post(ROTA, json=corpo, headers=auth_headers).status_code == 404


def test_time_fora_de_um_e_dois(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    """O Pydantic barra antes mesmo de chegar ao service."""
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores)
    corpo["participants"][0]["team"] = 3

    assert api.post(ROTA, json=corpo, headers=auth_headers).status_code == 422


# --------------------------------------------------------------------------
# Editar e excluir
# --------------------------------------------------------------------------


def test_edita_substituindo_a_escalacao(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    criada = api.post(ROTA, json=_corpo(jogadores, gols={0: 2}), headers=auth_headers).json()

    # Nova escalação: só dois jogadores, um em cada time, com outro placar.
    corpo = _corpo(jogadores[:2], placar=(1, 0), gols={0: 1})
    corpo["participants"][1]["team"] = 2
    corpo["team_1_name"] = "AZUL"

    resposta = api.put(f"{ROTA}/{criada['id']}", json=corpo, headers=auth_headers)

    assert resposta.status_code == 200
    atualizada = resposta.json()
    assert atualizada["team_1_name"] == "AZUL"
    assert len(atualizada["team_1"]) == 1
    assert len(atualizada["team_2"]) == 1


def test_edita_sem_token(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    criada = api.post(ROTA, json=_corpo(jogadores), headers=auth_headers).json()

    assert api.put(f"{ROTA}/{criada['id']}", json=_corpo(jogadores)).status_code == 401


def test_editar_atualiza_as_estatisticas_na_hora(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    """Como nada é contador guardado, o novo estado já vale na leitura seguinte."""
    jogadores = _quatro_jogadores(session)
    criada = api.post(ROTA, json=_corpo(jogadores, gols={0: 2}), headers=auth_headers).json()
    assert stats_service.player_stats(session, jogadores[0].id).goals == 2

    corpo = _corpo(jogadores, gols={0: 5})
    api.put(f"{ROTA}/{criada['id']}", json=corpo, headers=auth_headers)

    assert stats_service.player_stats(session, jogadores[0].id).goals == 5


def test_exclui_partida(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    criada = api.post(ROTA, json=_corpo(jogadores), headers=auth_headers).json()

    resposta = api.delete(f"{ROTA}/{criada['id']}", headers=auth_headers)

    assert resposta.status_code == 204
    assert api.get(f"{ROTA}/{criada['id']}").status_code == 404


def test_exclui_sem_token(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    criada = api.post(ROTA, json=_corpo(jogadores), headers=auth_headers).json()

    assert api.delete(f"{ROTA}/{criada['id']}").status_code == 401


def test_excluir_zera_o_impacto_nas_estatisticas(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    api.post(ROTA, json=_corpo(jogadores, data="2026-09-03", gols={0: 2}), headers=auth_headers)
    excluir = api.post(
        ROTA, json=_corpo(jogadores, data="2026-09-10", gols={0: 3}), headers=auth_headers
    ).json()
    assert stats_service.player_stats(session, jogadores[0].id).goals == 5

    api.delete(f"{ROTA}/{excluir['id']}", headers=auth_headers)

    depois = stats_service.player_stats(session, jogadores[0].id)
    assert depois.goals == 2
    assert depois.games == 1


def test_partida_inexistente(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogadores = _quatro_jogadores(session)
    inexistente = uuid.uuid4()

    assert api.put(
        f"{ROTA}/{inexistente}", json=_corpo(jogadores), headers=auth_headers
    ).status_code == 404
    assert api.delete(f"{ROTA}/{inexistente}", headers=auth_headers).status_code == 404


def test_agendada_sem_placar_e_aceita(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    """Agendar não exige resultado, e a partida fica fora das estatísticas."""
    jogadores = _quatro_jogadores(session)
    corpo = _corpo(jogadores, status="SCHEDULED", placar=(None, None))

    resposta = api.post(ROTA, json=corpo, headers=auth_headers)

    assert resposta.status_code == 201
    assert stats_service.player_stats(session, jogadores[0].id).games == 0
