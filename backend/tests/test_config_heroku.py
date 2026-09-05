"""Configuração que só o Heroku exercita: URL do banco, pool e R2.

A URL do banco é o ponto mais frágil da migração. O Heroku injeta
`DATABASE_URL` sozinho e a **reescreve** toda vez que rotaciona a credencial,
então não existe a opção de corrigi-la à mão uma vez e esquecer: ou a
aplicação aceita o formato dele, ou um dia ela para de subir sem ninguém ter
mexido em nada.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import ConfiguracaoInsegura, Settings, _validar_producao

CHAVE_BOA = "u" * 48


def _producao(**extras: object) -> Settings:
    return Settings(
        app_env="production",
        secret_key=CHAVE_BOA,
        database_url="postgresql+psycopg://migue:senha-forte@host:5432/migue",
        cors_origins="https://migue.herokuapp.com",
        **extras,
    )


# --------------------------------------------------------------------------
# DATABASE_URL
# --------------------------------------------------------------------------


def test_url_do_heroku_ganha_o_driver_e_ssl() -> None:
    """`postgres://` é o formato que o Heroku entrega — e o único que ele usa."""
    s = Settings(database_url="postgres://u:p@ec2.compute.amazonaws.com:5432/d")

    assert s.database_url.startswith("postgresql+psycopg://")
    assert "u:p@ec2.compute.amazonaws.com:5432/d" in s.database_url
    # Sem isto o psycopg negociaria TLS em modo "prefer", que aceita cair para
    # texto puro em silêncio.
    assert s.database_url.endswith("?sslmode=require")


def test_url_do_heroku_com_query_preserva_a_existente() -> None:
    s = Settings(database_url="postgres://u:p@h:5432/d?connect_timeout=10")

    assert s.database_url.endswith("?connect_timeout=10&sslmode=require")


def test_url_do_heroku_nao_duplica_sslmode() -> None:
    s = Settings(database_url="postgres://u:p@h:5432/d?sslmode=verify-full")

    assert s.database_url.count("sslmode=") == 1
    assert "verify-full" in s.database_url


def test_postgresql_sem_driver_ganha_o_driver_mas_nao_ssl() -> None:
    """`postgresql://` cairia no psycopg2, que não é dependência do projeto.

    O sslmode não entra aqui: esse formato também é o que alguém digita para
    apontar para um Postgres local, onde exigir TLS quebraria a conexão.
    """
    s = Settings(database_url="postgresql://migue:migue@db:5432/migue")

    assert s.database_url == "postgresql+psycopg://migue:migue@db:5432/migue"


def test_url_ja_correta_passa_intacta() -> None:
    url = "postgresql+psycopg://migue:migue@db:5432/migue"

    assert Settings(database_url=url).database_url == url


# --------------------------------------------------------------------------
# Pool
# --------------------------------------------------------------------------


def test_pool_cabe_no_essential_0() -> None:
    """2 workers x (pool + overflow) precisa sobrar folga dentro de ~20.

    Estourar o teto do plano não derruba o site na hora: ele falha só no pico,
    que é quando ninguém está olhando.
    """
    s = Settings()
    por_worker = s.db_pool_size + s.db_max_overflow

    assert por_worker * 2 <= 14


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------


def test_local_e_o_padrao() -> None:
    """Desenvolvimento não deve precisar de credencial de nuvem para rodar."""
    assert Settings().usa_r2 is False


def test_producao_com_r2_incompleto_nao_sobe() -> None:
    """Disco local num dyno é armadilha: funciona no teste e some no deploy."""
    with pytest.raises(ConfiguracaoInsegura) as erro:
        _validar_producao(_producao(storage_backend="r2", r2_bucket="migue-fotos"))

    mensagem = str(erro.value)
    assert "R2_ENDPOINT_URL" in mensagem
    assert "R2_ACCESS_KEY_ID" in mensagem
    assert "R2_BUCKET" not in mensagem


def test_producao_com_r2_completo_sobe() -> None:
    _validar_producao(
        _producao(
            storage_backend="r2",
            r2_endpoint_url="https://conta.r2.cloudflarestorage.com",
            r2_access_key_id="chave",
            r2_secret_access_key="segredo",
            r2_bucket="migue-fotos",
        )
    )


# --------------------------------------------------------------------------
# Frontend embutido
# --------------------------------------------------------------------------


def test_spa_dir_ignora_diretorio_sem_index(tmp_path: Path) -> None:
    """Montar um diretório vazio daria 404 em toda rota, sem pista da causa."""
    assert Settings(static_root=tmp_path).spa_dir is None


def test_spa_dir_aceita_diretorio_com_index(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")

    assert Settings(static_root=tmp_path).spa_dir == tmp_path


def test_sem_static_root_nao_ha_spa() -> None:
    assert Settings().spa_dir is None
