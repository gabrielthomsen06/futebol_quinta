"""Regras que moram nos services."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, DomainError
from app.models.enums import MatchStatus, RankingMetric
from app.services import match_service, player_service, stats_service
from app.services.match_service import ParticipantInput
from tests.conftest import criar_jogador, criar_partida


def test_piso_de_tres_jogos_vale_so_para_rankings_de_media(session: Session) -> None:
    """Sem piso, quem jogou uma vez e fez 3 gols lidera a média para sempre."""
    veterano = criar_jogador(session, "Veterano")
    estreante = criar_jogador(session, "Estreante")
    adversario = criar_jogador(session, "Carlos")

    # Veterano: 3 jogos, 3 gols (média 1,00).
    for dia in (3, 10, 17):
        criar_partida(
            session,
            data=dt.date(2026, 9, dia),
            placar=(2, 1),
            escalacao=[(veterano, 1, 1, 0), (adversario, 2, 0, 0)],
        )
    # Estreante: 1 jogo, 3 gols (média 3,00).
    criar_partida(
        session,
        data=dt.date(2026, 9, 24),
        placar=(3, 0),
        escalacao=[(estreante, 1, 3, 0), (adversario, 2, 0, 0)],
    )

    media = stats_service.ranking(session, RankingMetric.GOALS_PER_GAME)
    assert stats_service.min_games_for(RankingMetric.GOALS_PER_GAME) == 3
    assert estreante.id not in {e.player_id for e in media}
    assert veterano.id in {e.player_id for e in media}

    # Nos rankings sem piso ele continua aparecendo normalmente.
    for metrica in (RankingMetric.GOALS, RankingMetric.ASSISTS, RankingMetric.WINS, RankingMetric.GAMES):
        assert stats_service.min_games_for(metrica) == 0
        assert estreante.id in {e.player_id for e in stats_service.ranking(session, metrica)}


def test_ranking_tem_ordenacao_deterministica(session: Session) -> None:
    """Empate em gols: sobe quem tem menos jogos; depois, apelido."""
    adversario = criar_jogador(session, "Zagueiro")
    poucos_jogos = criar_jogador(session, "Bruno")
    muitos_jogos = criar_jogador(session, "Alberto")

    # Bruno: 2 gols em 1 jogo. Alberto: 2 gols em 2 jogos.
    criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(2, 0),
        escalacao=[(poucos_jogos, 1, 2, 0), (adversario, 2, 0, 0)],
    )
    for dia in (10, 17):
        criar_partida(
            session,
            data=dt.date(2026, 9, dia),
            placar=(1, 0),
            escalacao=[(muitos_jogos, 1, 1, 0), (adversario, 2, 0, 0)],
        )

    ranking = stats_service.ranking(session, RankingMetric.GOALS)
    posicoes = [e.player_id for e in ranking]
    # Mesmo com "Alberto" vindo antes no alfabeto, quem tem menos jogos sobe.
    assert posicoes.index(poucos_jogos.id) < posicoes.index(muitos_jogos.id)


def test_apelido_duplicado_vira_erro_legivel(session: Session) -> None:
    """409 com mensagem, em vez de estouro de constraint na cara do usuário."""
    player_service.create_player(session, nickname="Gabriel")

    with pytest.raises(ConflictError) as erro:
        player_service.create_player(session, nickname="  gabriel  ")

    assert "Gabriel" in str(erro.value.detail)


def test_excluir_partida_zera_o_impacto_dela(session: Session) -> None:
    """Requisito 17 — o CASCADE some com as participações e o agregado cai junto."""
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    manter = criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(5, 3),
        escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 0, 0)],
    )
    excluir = criar_partida(
        session,
        data=dt.date(2026, 9, 10),
        placar=(4, 0),
        escalacao=[(gabriel, 1, 3, 2), (carlos, 2, 0, 0)],
    )
    session.commit()

    antes = stats_service.player_stats(session, gabriel.id)
    assert (antes.games, antes.goals, antes.assists) == (2, 5, 3)

    match_service.delete_match(session, excluir.id)

    depois = stats_service.player_stats(session, gabriel.id)
    assert (depois.games, depois.goals, depois.assists) == (1, 2, 1)
    assert match_service.get_match(session, manter.id) is not None


def test_partida_realizada_exige_placar_e_os_dois_times(session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    session.commit()

    with pytest.raises(DomainError, match="placar"):
        match_service.create_match(
            session,
            match_date=dt.date(2026, 9, 3),
            status=MatchStatus.PLAYED,
            team_1_name="TIME 1",
            team_2_name="TIME 2",
            team_1_score=None,
            team_2_score=None,
            participants=[ParticipantInput(player_id=gabriel.id, team=1)],
        )

    with pytest.raises(DomainError, match="cada time"):
        match_service.create_match(
            session,
            match_date=dt.date(2026, 9, 3),
            status=MatchStatus.PLAYED,
            team_1_name="TIME 1",
            team_2_name="TIME 2",
            team_1_score=5,
            team_2_score=3,
            participants=[ParticipantInput(player_id=gabriel.id, team=1)],
        )


def test_jogador_repetido_na_escalacao_e_recusado(session: Session) -> None:
    gabriel = criar_jogador(session, "Gabriel")
    session.commit()

    with pytest.raises(DomainError, match="duas vezes"):
        match_service.create_match(
            session,
            match_date=dt.date(2026, 9, 3),
            status=MatchStatus.SCHEDULED,
            team_1_name="TIME 1",
            team_2_name="TIME 2",
            team_1_score=None,
            team_2_score=None,
            participants=[
                ParticipantInput(player_id=gabriel.id, team=1),
                ParticipantInput(player_id=gabriel.id, team=2),
            ],
        )


def test_edicao_que_falha_no_meio_nao_grava_nada(session: Session) -> None:
    """Requisito 21 — atomicidade.

    A edição apaga a escalação antiga e insere a nova. Se a inserção falhar no
    meio do caminho, a partida não pode ficar sem jogadores: tudo volta atrás.
    Aqui a falha é provocada com um número de gols acima do limite do
    SMALLINT, que só estoura no banco, depois do DELETE já ter acontecido.
    """
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    partida = criar_partida(
        session, placar=(5, 3), escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 0, 0)]
    )
    session.commit()

    with pytest.raises(DataError):
        match_service.replace_match(
            session,
            partida.id,
            match_date=dt.date(2026, 9, 3),
            status=MatchStatus.PLAYED,
            team_1_name="AZUL",
            team_2_name="BRANCO",
            team_1_score=9,
            team_2_score=9,
            participants=[
                ParticipantInput(player_id=gabriel.id, team=1, goals=40_000),
                ParticipantInput(player_id=carlos.id, team=2),
            ],
        )

    intacta = match_service.get_match(session, partida.id)
    assert intacta.team_1_name == "TIME 1"
    assert intacta.team_1_score == 5
    assert len(intacta.participations) == 2
    assert stats_service.player_stats(session, gabriel.id).goals == 2
