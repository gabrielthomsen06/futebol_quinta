"""Fixtures da suíte.

Os testes rodam contra um Postgres de verdade, num banco `migue_test`
separado. Não é preciosismo: as constraints, o FILTER das agregações e o
índice em expressão são específicos do Postgres, e é exatamente onde um
SQLite mentiria para nós.

O schema do banco de teste é criado pelo **Alembic**, não por create_all().
Assim cada execução também verifica que a migration produz o schema que os
testes exercitam.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.enums import MatchStatus, PlayerStatus
from app.models.match import Match
from app.models.participation import MatchParticipation
from app.models.player import Player

TEST_DB = "migue_test"


def _url_para(banco: str) -> str:
    base, _, _ = settings.database_url.rpartition("/")
    return f"{base}/{banco}"


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Cria o banco de teste do zero e aplica as migrations nele."""
    admin = create_engine(_url_para("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{TEST_DB}"'))
    admin.dispose()

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", _url_para(TEST_DB))
    command.upgrade(cfg, "head")

    test_engine = create_engine(_url_para(TEST_DB), future=True)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Uma transação por teste, revertida no final.

    join_transaction_mode="create_savepoint" faz o commit dos services virar
    liberação de savepoint, então a transação externa continua podendo voltar
    atrás — os testes ficam isolados sem recriar o schema a cada um.
    """
    connection = engine.connect()
    outer = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        future=True,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Cliente HTTP para os testes de fumaça, contra o banco de desenvolvimento."""
    return TestClient(app)


# --------------------------------------------------------------------------
# Fábricas — montam cenário sem repetir boilerplate em cada teste.
# --------------------------------------------------------------------------


def criar_jogador(
    session: Session, apelido: str, *, status: PlayerStatus = PlayerStatus.ACTIVE
) -> Player:
    player = Player(nickname=apelido, status=status)
    session.add(player)
    session.flush()
    return player


def criar_partida(
    session: Session,
    *,
    data: dt.date | None = None,
    status: MatchStatus = MatchStatus.PLAYED,
    placar: tuple[int | None, int | None] = (0, 0),
    escalacao: list[tuple[Player, int, int, int]] | None = None,
    team_1_name: str = "TIME 1",
    team_2_name: str = "TIME 2",
) -> Match:
    """Cria partida com escalação.

    `escalacao` é uma lista de (jogador, time, gols, assistências).
    """
    match = Match(
        match_date=data or dt.date(2026, 9, 3),
        status=status,
        team_1_name=team_1_name,
        team_2_name=team_2_name,
        team_1_score=placar[0],
        team_2_score=placar[1],
    )
    session.add(match)
    session.flush()

    for jogador, time, gols, assistencias in escalacao or []:
        session.add(
            MatchParticipation(
                match_id=match.id,
                player_id=jogador.id,
                team=time,
                goals=gols,
                assists=assistencias,
            )
        )
    session.flush()
    return match
