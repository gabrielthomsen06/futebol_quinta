"""Cloudflare R2: gravar, trocar, apagar — e o Content-Type das imagens.

Os testes falam com um cliente falso, não com o R2 de verdade. O que está
sendo verificado é o contrato: que o `R2Storage` chame o S3 com os argumentos
certos e devolva as mesmas respostas que o `LocalStorage` devolveria. Um teste
contra a rede seria mais lento, exigiria credencial e ainda assim não provaria
mais do que isto.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.player import Player
from app.services import storage as storage_module
from app.services.storage import R2Storage, _tipo_do_arquivo, get_storage
from tests.conftest import criar_jogador

BUCKET = "migue-fotos"


class ClienteFalso:
    """O bastante do S3 para os quatro métodos do contrato."""

    def __init__(self) -> None:
        self.objetos: dict[str, dict] = {}
        self.chamadas: list[tuple[str, dict]] = []

    def put_object(self, **kwargs: object) -> dict:
        self.chamadas.append(("put_object", kwargs))
        self.objetos[kwargs["Key"]] = dict(kwargs)
        return {}

    def head_object(self, **kwargs: object) -> dict:
        self.chamadas.append(("head_object", kwargs))
        if kwargs["Key"] not in self.objetos:
            raise ClientError(
                {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "HeadObject",
            )
        return {}

    def delete_object(self, **kwargs: object) -> dict:
        self.chamadas.append(("delete_object", kwargs))
        self.objetos.pop(kwargs["Key"], None)
        return {}

    def generate_presigned_url(self, operacao: str, Params: dict, ExpiresIn: int) -> str:  # noqa: N803
        self.chamadas.append(("generate_presigned_url", {"ExpiresIn": ExpiresIn}))
        return f"https://r2.exemplo/{Params['Key']}?assinada=1&expira={ExpiresIn}"


@pytest.fixture
def r2(monkeypatch: pytest.MonkeyPatch) -> ClienteFalso:
    """Liga o R2 falso e faz `get_storage()` escolher o R2Storage."""
    cliente = ClienteFalso()
    monkeypatch.setattr(storage_module, "get_r2_client", lambda: cliente)
    monkeypatch.setattr(settings, "storage_backend", "r2")
    monkeypatch.setattr(settings, "r2_bucket", BUCKET)
    monkeypatch.setattr(settings, "r2_public_base_url", "")
    return cliente


# --------------------------------------------------------------------------
# Seleção do backend
# --------------------------------------------------------------------------


def test_get_storage_segue_a_configuracao(r2: ClienteFalso) -> None:
    assert isinstance(get_storage(), R2Storage)


def test_get_storage_volta_ao_disco_sem_r2() -> None:
    assert not isinstance(get_storage(), R2Storage)


# --------------------------------------------------------------------------
# Gravar, existir, apagar
# --------------------------------------------------------------------------


def test_save_grava_com_o_content_type_da_imagem(r2: ClienteFalso) -> None:
    """Sem Content-Type correto o navegador se recusa a exibir a foto.

    O `.webp` não está na tabela de tipos de todo sistema, e é justamente o
    formato em que TODA foto é gravada — o padrão seria octet-stream.
    """
    R2Storage(BUCKET).save("players/abc-1234.webp", b"conteudo")

    enviado = r2.objetos["players/abc-1234.webp"]
    assert enviado["ContentType"] == "image/webp"
    assert enviado["Bucket"] == BUCKET
    assert enviado["Body"] == b"conteudo"


def test_save_marca_cache_longo(r2: ClienteFalso) -> None:
    """O nome carrega sufixo aleatório e nunca se repete: o conteúdo é imutável."""
    R2Storage(BUCKET).save("players/abc-1234.webp", b"conteudo")

    assert "immutable" in r2.objetos["players/abc-1234.webp"]["CacheControl"]


def test_tipo_desconhecido_cai_no_padrao() -> None:
    assert _tipo_do_arquivo("players/sem-extensao") == "application/octet-stream"


def test_exists_responde_pelos_dois_lados(r2: ClienteFalso) -> None:
    armazenamento = R2Storage(BUCKET)

    assert armazenamento.exists("players/x.webp") is False
    armazenamento.save("players/x.webp", b"a")
    assert armazenamento.exists("players/x.webp") is True


def test_delete_devolve_se_havia_o_que_apagar(r2: ClienteFalso) -> None:
    """Mesma semântica do disco.

    O `delete_object` do S3 responde sucesso mesmo para chave inexistente; se
    o R2Storage repassasse isso, ele mentiria onde o LocalStorage diz a verdade.
    """
    armazenamento = R2Storage(BUCKET)
    armazenamento.save("players/x.webp", b"a")

    assert armazenamento.delete("players/x.webp") is True
    assert armazenamento.delete("players/x.webp") is False
    assert armazenamento.exists("players/x.webp") is False


def test_erro_que_nao_e_404_nao_vira_arquivo_ausente(
    r2: ClienteFalso, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Credencial errada não pode ser confundida com foto inexistente."""

    def negado(**_: object) -> dict:
        raise ClientError(
            {"Error": {"Code": "403"}, "ResponseMetadata": {"HTTPStatusCode": 403}},
            "HeadObject",
        )

    monkeypatch.setattr(r2, "head_object", negado)

    with pytest.raises(ClientError):
        R2Storage(BUCKET).exists("players/x.webp")


# --------------------------------------------------------------------------
# URL
# --------------------------------------------------------------------------


def test_url_assinada_quando_o_bucket_e_fechado(r2: ClienteFalso) -> None:
    url = R2Storage(BUCKET).url_for("players/x.webp")

    assert url.startswith("https://r2.exemplo/players/x.webp")
    assert "assinada=1" in url


def test_url_publica_quando_configurada(
    r2: ClienteFalso, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "r2_public_base_url", "https://fotos.migue.app/")

    assert (
        R2Storage(BUCKET).url_for("players/x.webp")
        == "https://fotos.migue.app/players/x.webp"
    )
    assert ("generate_presigned_url", {"ExpiresIn": 3600}) not in r2.chamadas


# --------------------------------------------------------------------------
# O fluxo inteiro do jogador, com o R2 no lugar do disco
# --------------------------------------------------------------------------


def _imagem() -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (800, 600), (242, 107, 33)).save(buffer, "JPEG")
    return buffer.getvalue()


def test_upload_troca_e_remocao_pelo_r2(
    session: Session, r2: ClienteFalso
) -> None:
    """O `photo_service` não sabe onde grava — e é isso que está sendo provado.

    Nenhuma linha dele mudou na Fase 12; o teste percorre upload, troca e
    remoção só para confirmar que a ordem que mantém banco e arquivo coerentes
    continua valendo quando o "disco" está do outro lado da rede.
    """
    from app.services.photo_service import remove_player_photo, store_player_photo

    jogador: Player = criar_jogador(session, "Gabriel")
    session.flush()

    store_player_photo(session, jogador, BytesIO(_imagem()))
    primeiro = jogador.photo_path
    assert primeiro is not None
    assert primeiro in r2.objetos
    assert r2.objetos[primeiro]["ContentType"] == "image/webp"

    store_player_photo(session, jogador, BytesIO(_imagem()))
    segundo = jogador.photo_path
    assert segundo != primeiro
    # A anterior sai só depois que o banco já aponta para a nova.
    assert primeiro not in r2.objetos
    assert segundo in r2.objetos

    remove_player_photo(session, jogador)
    assert jogador.photo_path is None
    assert r2.objetos == {}
