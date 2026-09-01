"""Fixtures compartilhadas.

Na Fase 2 os testes são de fumaça: exercitam a aplicação de pé contra o Postgres
do compose. As fixtures de banco isolado por transação entram na Fase 12, junto
com os testes de regra de negócio.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
