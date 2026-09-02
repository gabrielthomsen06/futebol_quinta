"""Jogadores: escrita autenticada, foto e a coerência entre disco e banco."""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.player import Player
from app.models.user import User
from tests.conftest import criar_jogador

ROTA = "/api/players"


def _imagem(largura: int = 800, altura: int = 600, formato: str = "JPEG") -> bytes:
    """Uma imagem de verdade, não um punhado de bytes com nome de foto."""
    buffer = BytesIO()
    Image.new("RGB", (largura, altura), (242, 107, 33)).save(buffer, formato)
    return buffer.getvalue()


def _enviar_foto(
    api: TestClient, player_id: uuid.UUID, headers: dict[str, str], conteudo: bytes,
    nome: str = "foto.jpg", tipo: str = "image/jpeg",
):
    return api.post(
        f"{ROTA}/{player_id}/photo",
        headers=headers,
        files={"foto": (nome, conteudo, tipo)},
    )


# --------------------------------------------------------------------------
# Criar, editar, status
# --------------------------------------------------------------------------


def test_cria_jogador(api: TestClient, auth_headers: dict[str, str]) -> None:
    resposta = api.post(ROTA, json={"nickname": "Gabriel"}, headers=auth_headers)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nickname"] == "Gabriel"
    assert corpo["status"] == "ACTIVE"
    assert corpo["photo_path"] is None


def test_cria_sem_token(api: TestClient) -> None:
    assert api.post(ROTA, json={"nickname": "Gabriel"}).status_code == 401


def test_apelido_duplicado(api: TestClient, auth_headers: dict[str, str]) -> None:
    api.post(ROTA, json={"nickname": "Gabriel"}, headers=auth_headers)

    resposta = api.post(ROTA, json={"nickname": "Gabriel"}, headers=auth_headers)

    assert resposta.status_code == 409
    assert "Gabriel" in resposta.json()["detail"]


def test_apelido_duplicado_ignorando_caixa(
    api: TestClient, auth_headers: dict[str, str]
) -> None:
    """"gabriel" e "Gabriel" seriam dois jogadores idênticos na tela."""
    api.post(ROTA, json={"nickname": "Gabriel"}, headers=auth_headers)

    resposta = api.post(ROTA, json={"nickname": "  gabriel  "}, headers=auth_headers)

    assert resposta.status_code == 409


def test_apelido_vazio(api: TestClient, auth_headers: dict[str, str]) -> None:
    assert api.post(ROTA, json={"nickname": ""}, headers=auth_headers).status_code == 422


def test_edita_apelido(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogador = criar_jogador(session, "Gabriel")

    resposta = api.put(
        f"{ROTA}/{jogador.id}", json={"nickname": "Gabi"}, headers=auth_headers
    )

    assert resposta.status_code == 200
    assert resposta.json()["nickname"] == "Gabi"


def test_edita_sem_token(api: TestClient, session: Session) -> None:
    jogador = criar_jogador(session, "Gabriel")

    assert api.put(f"{ROTA}/{jogador.id}", json={"nickname": "Gabi"}).status_code == 401


def test_edita_para_apelido_ja_usado(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    criar_jogador(session, "Carlos")
    jogador = criar_jogador(session, "Gabriel")

    resposta = api.put(
        f"{ROTA}/{jogador.id}", json={"nickname": "Carlos"}, headers=auth_headers
    )

    assert resposta.status_code == 409


def test_ativa_e_inativa(
    api: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    jogador = criar_jogador(session, "Gabriel")
    rota = f"{ROTA}/{jogador.id}/status"

    inativado = api.patch(rota, json={"status": "INACTIVE"}, headers=auth_headers)
    assert inativado.status_code == 200
    assert inativado.json()["status"] == "INACTIVE"

    reativado = api.patch(rota, json={"status": "ACTIVE"}, headers=auth_headers)
    assert reativado.json()["status"] == "ACTIVE"


def test_status_sem_token(api: TestClient, session: Session) -> None:
    jogador = criar_jogador(session, "Gabriel")

    resposta = api.patch(f"{ROTA}/{jogador.id}/status", json={"status": "INACTIVE"})

    assert resposta.status_code == 401


def test_inativo_fora_do_padrao_e_presente_em_todos(
    api: TestClient, session: Session
) -> None:
    """Inativar é sobre a próxima partida, não sobre esconder o jogador."""
    from app.models.enums import PlayerStatus

    criar_jogador(session, "Ativo")
    criar_jogador(session, "Inativo", status=PlayerStatus.INACTIVE)
    session.commit()

    padrao = {p["nickname"] for p in api.get(ROTA).json()}
    todos = {p["nickname"] for p in api.get(f"{ROTA}?status=all").json()}
    so_inativos = {p["nickname"] for p in api.get(f"{ROTA}?status=inactive").json()}

    assert padrao == {"Ativo"}
    assert todos == {"Ativo", "Inativo"}
    assert so_inativos == {"Inativo"}


def test_nao_existe_exclusao_de_jogador(api: TestClient, session: Session) -> None:
    """Jogador não se apaga: o histórico depende dele."""
    jogador = criar_jogador(session, "Gabriel")
    session.commit()

    assert api.delete(f"{ROTA}/{jogador.id}").status_code == 405


# --------------------------------------------------------------------------
# Foto
# --------------------------------------------------------------------------


def test_upload_grava_webp_quadrado(
    api: TestClient,
    session: Session,
    auth_headers: dict[str, str],
    media_tmp: Path,
) -> None:
    """Entra um JPEG 800x600; sai um WEBP 512x512."""
    jogador = criar_jogador(session, "Gabriel")
    session.commit()

    resposta = _enviar_foto(api, jogador.id, auth_headers, _imagem())

    assert resposta.status_code == 200
    caminho = resposta.json()["photo_path"]
    assert caminho.startswith(f"players/{jogador.id}-")
    assert caminho.endswith(".webp")

    arquivo = media_tmp / caminho
    assert arquivo.exists()
    with Image.open(arquivo) as gravada:
        assert gravada.format == "WEBP"
        assert gravada.size == (settings.photo_size, settings.photo_size)


def test_upload_recusa_arquivo_que_nao_e_imagem(
    api: TestClient, session: Session, auth_headers: dict[str, str], media_tmp: Path
) -> None:
    """Extensão de imagem com conteúdo de texto não engana a validação."""
    jogador = criar_jogador(session, "Gabriel")
    session.commit()

    resposta = _enviar_foto(api, jogador.id, auth_headers, b"isto aqui e texto puro")

    assert resposta.status_code == 400
    assert "imagem" in resposta.json()["detail"].lower()
    assert list(media_tmp.glob("players/*")) == []


def test_upload_recusa_heic_com_mensagem_util(
    api: TestClient, session: Session, auth_headers: dict[str, str], media_tmp: Path
) -> None:
    """HEIC é o padrão do iPhone: o erro precisa dizer o que fazer."""
    jogador = criar_jogador(session, "Gabriel")
    session.commit()
    heic = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 64

    resposta = _enviar_foto(api, jogador.id, auth_headers, heic, "foto.heic", "image/heic")

    assert resposta.status_code == 400
    assert "HEIC" in resposta.json()["detail"]
    assert "JPEG" in resposta.json()["detail"]


def test_upload_recusa_arquivo_grande(
    api: TestClient, session: Session, auth_headers: dict[str, str], media_tmp: Path
) -> None:
    jogador = criar_jogador(session, "Gabriel")
    session.commit()
    grande = b"\xff\xd8\xff" + b"\x00" * (settings.max_photo_bytes + 1)

    resposta = _enviar_foto(api, jogador.id, auth_headers, grande)

    assert resposta.status_code == 400
    assert "MB" in resposta.json()["detail"]
    assert list(media_tmp.glob("players/*")) == []


def test_upload_sem_token(api: TestClient, session: Session, media_tmp: Path) -> None:
    jogador = criar_jogador(session, "Gabriel")
    session.commit()

    resposta = api.post(
        f"{ROTA}/{jogador.id}/photo", files={"foto": ("f.jpg", _imagem(), "image/jpeg")}
    )

    assert resposta.status_code == 401


def test_trocar_foto_apaga_a_anterior(
    api: TestClient, session: Session, auth_headers: dict[str, str], media_tmp: Path
) -> None:
    """O arquivo antigo não pode ficar ocupando espaço para sempre."""
    jogador = criar_jogador(session, "Gabriel")
    session.commit()

    primeira = _enviar_foto(api, jogador.id, auth_headers, _imagem()).json()["photo_path"]
    segunda = _enviar_foto(api, jogador.id, auth_headers, _imagem(400, 400)).json()[
        "photo_path"
    ]

    assert primeira != segunda  # nome novo a cada upload, senão o cache engana
    assert not (media_tmp / primeira).exists()
    assert (media_tmp / segunda).exists()
    assert list((media_tmp / "players").iterdir()) == [media_tmp / segunda]


def test_remover_foto_zera_o_caminho_e_o_arquivo(
    api: TestClient, session: Session, auth_headers: dict[str, str], media_tmp: Path
) -> None:
    jogador = criar_jogador(session, "Gabriel")
    session.commit()
    caminho = _enviar_foto(api, jogador.id, auth_headers, _imagem()).json()["photo_path"]

    resposta = api.delete(f"{ROTA}/{jogador.id}/photo", headers=auth_headers)

    assert resposta.status_code == 200
    assert resposta.json()["photo_path"] is None
    assert not (media_tmp / caminho).exists()


def test_falha_ao_gravar_no_banco_nao_deixa_arquivo_orfao(
    session: Session, media_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A regra de consistência: o banco manda, o disco segue.

    Se o commit falhar depois de o arquivo já ter sido gravado, o arquivo novo
    precisa sumir — senão sobra um órfão que ninguém referencia — e a foto
    anterior tem de continuar valendo.
    """
    from app.services import photo_service

    jogador = criar_jogador(session, "Gabriel")
    jogador.photo_path = "players/foto-anterior.webp"
    session.flush()

    @contextmanager
    def transacao_que_falha(_sessao):  # type: ignore[no-untyped-def]
        raise RuntimeError("banco indisponível")
        yield  # pragma: no cover

    monkeypatch.setattr(photo_service, "transaction", transacao_que_falha)

    with pytest.raises(RuntimeError):
        photo_service.store_player_photo(session, jogador, BytesIO(_imagem()))

    assert list(media_tmp.glob("players/*")) == []
    assert jogador.photo_path == "players/foto-anterior.webp"
