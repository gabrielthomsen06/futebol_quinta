"""Foto do jogador: validação, normalização e a ordem que mantém disco e banco juntos.

**Consistência.** Duas falhas são possíveis e uma é muito pior que a outra:

  - referência quebrada — `photo_path` aponta para arquivo que não existe;
  - arquivo órfão — arquivo no disco que ninguém referencia.

A referência quebrada aparece para quem usa; o órfão só ocupa alguns kilobytes.
Por isso **o banco é a fonte da verdade e o disco é ajustado para segui-lo**, o
que na prática define a ordem das operações: grava o arquivo novo, commita, e só
depois apaga o antigo.
"""

from __future__ import annotations

import logging
import secrets
from io import BytesIO
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DomainError
from app.db.session import transaction
from app.models.player import Player
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

FORMATOS_ACEITOS = frozenset({"JPEG", "PNG", "WEBP"})
_BLOCO = 64 * 1024


def _ler_limitado(arquivo: BinaryIO, limite: int) -> bytes:
    """Lê em blocos, abortando assim que passar do limite.

    Ler tudo e só então conferir o tamanho carregaria na memória exatamente o
    arquivo gigante que queremos recusar.
    """
    blocos: list[bytes] = []
    total = 0
    while True:
        bloco = arquivo.read(_BLOCO)
        if not bloco:
            break
        total += len(bloco)
        if total > limite:
            megabytes = limite // (1024 * 1024)
            raise DomainError(f"A foto precisa ter no máximo {megabytes} MB.")
        blocos.append(bloco)
    return b"".join(blocos)


def _parece_heic(bruto: bytes) -> bool:
    """Detecta HEIC pelos bytes, para dar um erro que ajuda.

    É o formato padrão do iPhone, e o Pillow não o lê sem `pillow-heif`. Sem
    esta checagem a pessoa receberia só "não é uma imagem", que não diz o que
    fazer.
    """
    return len(bruto) > 12 and bruto[4:8] == b"ftyp" and bruto[8:12] in {
        b"heic",
        b"heix",
        b"hevc",
        b"mif1",
        b"msf1",
    }


def _normalizar(bruto: bytes, tamanho: int) -> bytes:
    """Valida pelos bytes e devolve um WEBP quadrado.

    O reencode padroniza peso e dimensão, descarta o EXIF — incluindo a
    localização de onde a foto foi tirada — e neutraliza arquivo malicioso
    disfarçado de imagem.
    """
    if _parece_heic(bruto):
        raise DomainError(
            "Fotos HEIC (padrão do iPhone) não são aceitas. "
            "Converta para JPEG antes de enviar."
        )

    try:
        imagem = Image.open(BytesIO(bruto))
    except UnidentifiedImageError as erro:
        raise DomainError("O arquivo enviado não é uma imagem.") from erro

    formato = (imagem.format or "").upper()
    if formato not in FORMATOS_ACEITOS:
        raise DomainError(f"Formato {formato or 'desconhecido'} não aceito. Envie JPEG, PNG ou WEBP.")

    try:
        # Sem isto, foto tirada de celular sai deitada: a orientação vive no
        # EXIF, e o recorte a seguir ignoraria essa informação.
        imagem = ImageOps.exif_transpose(imagem) or imagem
        imagem = imagem.convert("RGB")
        # fit() recorta o centro e redimensiona numa passada só.
        imagem = ImageOps.fit(imagem, (tamanho, tamanho), Image.Resampling.LANCZOS)

        saida = BytesIO()
        imagem.save(saida, "WEBP", quality=85, method=6)
        return saida.getvalue()
    except OSError as erro:
        raise DomainError("Não foi possível processar esta imagem.") from erro


def _caminho_novo(player: Player) -> str:
    """Nome sempre diferente a cada upload.

    Reaproveitar o nome faria o navegador continuar exibindo a foto antiga, que
    já está no cache dele.
    """
    return f"players/{player.id}-{secrets.token_hex(4)}.webp"


def store_player_photo(session: Session, player: Player, arquivo: BinaryIO) -> Player:
    """Troca a foto do jogador, mantendo disco e banco coerentes."""
    bruto = _ler_limitado(arquivo, settings.max_photo_bytes)
    if not bruto:
        raise DomainError("O arquivo enviado está vazio.")

    imagem = _normalizar(bruto, settings.photo_size)

    armazenamento = get_storage()
    caminho_antigo = player.photo_path
    caminho_novo = _caminho_novo(player)

    # 1. Grava o novo. Como o nome é inédito, a foto atual segue intacta.
    armazenamento.save(caminho_novo, imagem)

    # 2. Só então o banco passa a apontar para ele.
    try:
        with transaction(session):
            player.photo_path = caminho_novo
    except Exception:
        # Commit falhou: desfaz o arquivo recém-gravado para não deixar órfão,
        # e a foto anterior continua valendo.
        armazenamento.delete(caminho_novo)
        raise

    # 3. Com o banco já correto, o arquivo antigo pode ir embora. Se essa
    #    remoção falhar, sobra um órfão inofensivo — não é motivo para
    #    derrubar uma requisição que já deu certo.
    if caminho_antigo:
        try:
            armazenamento.delete(caminho_antigo)
        except OSError:
            logger.warning("Não foi possível remover a foto antiga %s", caminho_antigo)

    session.refresh(player)
    return player


def remove_player_photo(session: Session, player: Player) -> Player:
    """Remove a foto. Sem foto, a interface mostra as iniciais do apelido."""
    caminho = player.photo_path
    if caminho is None:
        return player

    # Zera no banco primeiro: apagar o arquivo antes deixaria uma referência
    # quebrada caso o commit falhasse.
    with transaction(session):
        player.photo_path = None

    try:
        get_storage().delete(caminho)
    except OSError:
        logger.warning("Não foi possível remover a foto %s", caminho)

    session.refresh(player)
    return player
