"""O que o Caddy garantia e agora é responsabilidade da aplicação.

Na VPS, cabeçalhos de segurança, compressão, redirecionamento para HTTPS e o
fallback de SPA eram do proxy. No Heroku o roteador só termina o TLS. Estes
testes existem para que a migração não troque a stack de produção por uma
versão dela sem proteção nenhuma — uma perda que não aparece na tela.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import media
from app.core.middleware import (
    CABECALHOS_DE_SEGURANCA,
    ForceHTTPSMiddleware,
    SPAStaticFiles,
    SecurityHeadersMiddleware,
)


# --------------------------------------------------------------------------
# Cabeçalhos de segurança — na aplicação de verdade
# --------------------------------------------------------------------------


def test_aplicacao_real_devolve_os_cabecalhos(client: TestClient) -> None:
    """Os mesmos quatro que estavam no Caddyfile, para não mudar a política."""
    cabecalhos = client.get("/api/health").headers

    for nome, valor in CABECALHOS_DE_SEGURANCA.items():
        assert cabecalhos.get(nome) == valor


def test_aplicacao_real_comprime_resposta_grande(client: TestClient) -> None:
    """`encode zstd gzip` do Caddy vira o GZipMiddleware."""
    resposta = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})

    assert resposta.status_code == 200
    assert resposta.headers.get("content-encoding") == "gzip"


def test_cabecalho_ja_definido_nao_e_sobrescrito() -> None:
    """Uma rota que precise afrouxar X-Frame-Options continua podendo."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/embutivel")
    def embutivel():  # noqa: ANN202
        from fastapi.responses import JSONResponse

        return JSONResponse({}, headers={"X-Frame-Options": "SAMEORIGIN"})

    assert (
        TestClient(app).get("/embutivel").headers["X-Frame-Options"] == "SAMEORIGIN"
    )


# --------------------------------------------------------------------------
# HTTPS
# --------------------------------------------------------------------------


@pytest.fixture
def app_https() -> TestClient:
    app = FastAPI()
    app.add_middleware(ForceHTTPSMiddleware)

    @app.get("/rankings")
    def rankings() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app, base_url="http://testserver")


def test_http_redireciona_para_https(app_https: TestClient) -> None:
    """O Heroku entrega em HTTP simples; o esquema real vem no cabeçalho."""
    resposta = app_https.get(
        "/rankings", headers={"X-Forwarded-Proto": "http"}, follow_redirects=False
    )

    # 308 preserva o método: um POST redirecionado não vira GET.
    assert resposta.status_code == 308
    assert resposta.headers["location"] == "https://testserver/rankings"


def test_https_passa_direto(app_https: TestClient) -> None:
    resposta = app_https.get("/rankings", headers={"X-Forwarded-Proto": "https"})

    assert resposta.status_code == 200


def test_lista_de_proxies_usa_o_primeiro(app_https: TestClient) -> None:
    """Com mais de um proxy o cabeçalho vira lista; o cliente é o primeiro."""
    resposta = app_https.get(
        "/rankings",
        headers={"X-Forwarded-Proto": "https, http"},
        follow_redirects=False,
    )

    assert resposta.status_code == 200


# --------------------------------------------------------------------------
# Fallback de SPA
# --------------------------------------------------------------------------


@pytest.fixture
def app_spa(tmp_path: Path) -> TestClient:
    (tmp_path / "index.html").write_text("<html>MIGUE SPA</html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")

    app = FastAPI()

    @app.get("/api/health")
    def saude() -> dict[str, str]:
        return {"status": "ok"}

    app.mount("/", SPAStaticFiles(tmp_path), name="spa")
    return TestClient(app)


def test_f5_em_rota_interna_devolve_o_app(app_spa: TestClient) -> None:
    """Era o `try_files {path} /index.html`. Sem ele, F5 em /rankings dá 404."""
    resposta = app_spa.get("/rankings")

    assert resposta.status_code == 200
    assert "MIGUE SPA" in resposta.text


def test_f5_em_rota_profunda_devolve_o_app(app_spa: TestClient) -> None:
    resposta = app_spa.get("/jogadores/8f14e45f-ceea-467a-9575-28d8f6c0dbc0")

    assert resposta.status_code == 200
    assert "MIGUE SPA" in resposta.text


def test_arquivo_existente_e_servido_como_arquivo(app_spa: TestClient) -> None:
    resposta = app_spa.get("/assets/app.js")

    assert resposta.status_code == 200
    assert resposta.text == "console.log(1)"


def test_rota_de_api_continua_ganhando_do_spa(app_spa: TestClient) -> None:
    assert app_spa.get("/api/health").json() == {"status": "ok"}


def test_api_inexistente_devolve_404_e_nao_o_index(app_spa: TestClient) -> None:
    """Devolver o React num /api errado faria a rota parecer que funcionou."""
    resposta = app_spa.get("/api/rota-que-nao-existe")

    assert resposta.status_code == 404
    assert "MIGUE SPA" not in resposta.text


def test_media_inexistente_tambem_nao_vira_index(app_spa: TestClient) -> None:
    assert app_spa.get("/media/players/nao-existe.webp").status_code == 404


# --------------------------------------------------------------------------
# /media com as fotos fora da aplicação
# --------------------------------------------------------------------------


class StorageFalso:
    def url_for(self, rel_path: str) -> str:
        return f"https://r2.exemplo/{rel_path}?assinada=1"


@pytest.fixture
def app_media(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(media, "get_storage", StorageFalso)
    app = FastAPI()
    app.include_router(media.router, prefix="/media")
    return TestClient(app)


def test_media_redireciona_para_o_r2(app_media: TestClient) -> None:
    """O frontend continua pedindo /media/<caminho>; quem sabe o resto é a API."""
    resposta = app_media.get(
        "/media/players/abc-1234.webp", follow_redirects=False
    )

    assert resposta.status_code == 302
    assert (
        resposta.headers["location"]
        == "https://r2.exemplo/players/abc-1234.webp?assinada=1"
    )


def test_media_recusa_caminho_que_sobe_de_diretorio(app_media: TestClient) -> None:
    resposta = app_media.get("/media/../etc/senha", follow_redirects=False)

    assert resposta.status_code == 404
