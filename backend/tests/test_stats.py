"""Estatísticas derivadas — o coração do sistema.

Toda asserção aqui parte de partidas cruas e confere o que a consulta agregada
devolve. Nenhum número é lido de contador.
"""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus, PlayerStatus
from app.services import stats_service
from tests.conftest import criar_jogador, criar_partida


def _stats(session: Session, jogador, **kwargs):  # type: ignore[no-untyped-def]
    return stats_service.player_stats(session, jogador.id, **kwargs)


def test_jogador_participa_de_varias_partidas(session: Session) -> None:
    """Requisito 1."""
    gabriel = criar_jogador(session, "Gabriel")
    adversario = criar_jogador(session, "Carlos")

    for dia, gols in ((3, 2), (10, 1), (17, 3)):
        criar_partida(
            session,
            data=dt.date(2026, 9, dia),
            placar=(4, 1),
            escalacao=[(gabriel, 1, gols, 1), (adversario, 2, 0, 0)],
        )

    stats = _stats(session, gabriel)
    assert stats.games == 3
    assert stats.goals == 6
    assert stats.assists == 3


def test_partida_agendada_nao_entra_nas_estatisticas(session: Session) -> None:
    """Requisito 7."""
    gabriel = criar_jogador(session, "Gabriel")
    criar_partida(
        session,
        status=MatchStatus.SCHEDULED,
        placar=(None, None),
        escalacao=[(gabriel, 1, 0, 0)],
    )

    stats = _stats(session, gabriel)
    assert stats.games == 0
    assert stats.goals == 0
    assert stats.wins == 0


def test_partida_cancelada_nao_entra_nas_estatisticas(session: Session) -> None:
    """Requisito 8.

    O placar continua guardado no banco — cancelar e voltar atrás não perde o
    que já foi digitado — mas é completamente ignorado enquanto o status não
    for PLAYED.
    """
    gabriel = criar_jogador(session, "Gabriel")
    partida = criar_partida(
        session,
        status=MatchStatus.CANCELLED,
        placar=(5, 3),
        escalacao=[(gabriel, 1, 2, 1)],
    )

    stats = _stats(session, gabriel)
    assert stats.games == 0
    assert stats.goals == 0
    # O dado permanece no banco, apenas fora da conta.
    assert partida.team_1_score == 5


def test_partida_realizada_entra_nas_estatisticas(session: Session) -> None:
    """Requisito 9."""
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session,
        placar=(5, 3),
        escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 3, 0)],
    )

    gabriel_stats = _stats(session, gabriel)
    assert (gabriel_stats.games, gabriel_stats.goals, gabriel_stats.assists) == (1, 2, 1)
    assert gabriel_stats.wins == 1
    assert gabriel_stats.goal_participations == 3


def test_gols_individuais_nao_precisam_bater_com_o_placar(session: Session) -> None:
    """Requisito 10 — a regra mais importante, e ela é uma ausência.

    Placar 6x4, mas só 4 gols anotados na folha. Isso é registro válido: o
    placar é o resultado oficial e os gols individuais são independentes.
    Nenhuma camada — banco, schema ou service — pode reclamar disso.
    """
    gabriel = criar_jogador(session, "Gabriel")
    joao = criar_jogador(session, "João")
    pedro = criar_jogador(session, "Pedro")
    carlos = criar_jogador(session, "Carlos")

    criar_partida(
        session,
        placar=(6, 4),
        escalacao=[
            (gabriel, 1, 2, 1),
            (joao, 1, 1, 2),
            (pedro, 1, 1, 0),
            (carlos, 2, 0, 0),
        ],
    )

    soma_do_time_1 = sum(_stats(session, j).goals for j in (gabriel, joao, pedro))
    assert soma_do_time_1 == 4  # e o placar diz 6
    assert _stats(session, gabriel).wins == 1


@pytest.mark.parametrize(
    ("placar", "time_do_jogador", "esperado"),
    [
        ((5, 3), 1, "vitoria"),
        ((5, 3), 2, "derrota"),
        ((2, 2), 1, "empate"),
        ((2, 2), 2, "empate"),
        ((1, 4), 1, "derrota"),
        ((1, 4), 2, "vitoria"),
    ],
)
def test_vitoria_empate_derrota_saem_do_placar(
    session: Session,
    placar: tuple[int, int],
    time_do_jogador: int,
    esperado: str,
) -> None:
    """Requisito 11 — os seis cruzamentos de placar e lado."""
    jogador = criar_jogador(session, "Gabriel")
    criar_partida(session, placar=placar, escalacao=[(jogador, time_do_jogador, 0, 0)])

    stats = _stats(session, jogador)
    resultados = {
        "vitoria": (1, 0, 0),
        "empate": (0, 1, 0),
        "derrota": (0, 0, 1),
    }
    assert (stats.wins, stats.draws, stats.losses) == resultados[esperado]


def test_jogador_inativo_mantem_historico(session: Session) -> None:
    """Requisito 12.

    Inativar é sobre a próxima partida, não sobre o passado: ele fez aqueles
    gols, e o histórico não muda porque parou de jogar.
    """
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    criar_partida(
        session, placar=(5, 3), escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 1, 0)]
    )

    antes = _stats(session, gabriel)
    gabriel.status = PlayerStatus.INACTIVE
    session.flush()
    depois = _stats(session, gabriel)

    assert (antes.games, antes.goals, antes.wins) == (depois.games, depois.goals, depois.wins)
    assert depois.status is PlayerStatus.INACTIVE

    # E continua presente nos rankings históricos.
    from app.models.enums import RankingMetric

    ranking = stats_service.ranking(session, RankingMetric.GOALS)
    assert gabriel.id in {e.player_id for e in ranking}


def test_jogador_sem_partida_aparece_zerado(session: Session) -> None:
    """O LEFT JOIN tem que trazê-lo, e a média não pode dividir por zero."""
    novato = criar_jogador(session, "Novato")

    stats = _stats(session, novato)
    assert stats.games == 0
    assert stats.goals_per_game == 0.0
    assert stats.assists_per_game == 0.0
    assert stats.win_rate == 0.0


def test_filtro_de_periodo_recorta_o_agregado(session: Session) -> None:
    """Base dos filtros de temporada e de mês."""
    gabriel = criar_jogador(session, "Gabriel")
    criar_partida(
        session, data=dt.date(2026, 8, 27), placar=(3, 1), escalacao=[(gabriel, 1, 1, 0)]
    )
    criar_partida(
        session, data=dt.date(2026, 9, 3), placar=(5, 3), escalacao=[(gabriel, 1, 2, 1)]
    )

    setembro = _stats(session, gabriel, date_from=dt.date(2026, 9, 1))
    assert setembro.games == 1
    assert setembro.goals == 2

    tudo = _stats(session, gabriel)
    assert tudo.games == 2
    assert tudo.goals == 3


def test_medias_e_aproveitamento(session: Session) -> None:
    """As derivadas em cima do agregado."""
    gabriel = criar_jogador(session, "Gabriel")
    carlos = criar_jogador(session, "Carlos")
    # Duas vitórias e uma derrota, 4 gols e 2 assistências em 3 jogos.
    criar_partida(
        session,
        data=dt.date(2026, 9, 3),
        placar=(5, 3),
        escalacao=[(gabriel, 1, 2, 1), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session,
        data=dt.date(2026, 9, 10),
        placar=(2, 1),
        escalacao=[(gabriel, 1, 1, 1), (carlos, 2, 0, 0)],
    )
    criar_partida(
        session,
        data=dt.date(2026, 9, 17),
        placar=(0, 2),
        escalacao=[(gabriel, 1, 1, 0), (carlos, 2, 0, 0)],
    )

    stats = _stats(session, gabriel)
    assert stats.games == 3
    assert stats.goals == 4
    assert stats.goals_per_game == round(4 / 3, 2)
    assert stats.assists_per_game == round(2 / 3, 2)
    assert stats.win_rate == round(2 / 3 * 100, 1)
