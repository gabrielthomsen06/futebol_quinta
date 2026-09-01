"""Testes de fumaça da Fase 2: a aplicação sobe e enxerga o banco."""

from fastapi.testclient import TestClient


def test_health_responde_ok_com_banco_acessivel(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["season"] == 2026


def test_health_tambem_responde_sem_o_prefixo_api(client: TestClient) -> None:
    """O healthcheck do container usa /health direto."""
    assert client.get("/health").status_code == 200


def test_raiz_aponta_para_a_documentacao(client: TestClient) -> None:
    body = client.get("/").json()

    assert body["docs"] == "/docs"


def test_openapi_e_gerado(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/api/health" in schema["paths"]
