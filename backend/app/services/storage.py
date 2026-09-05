"""Armazenamento de arquivos.

A interface existe para que trocar disco local por S3 seja escrever outra
classe, sem nenhum service mudar. O banco guarda apenas o caminho relativo,
então a troca também não exige migração de dados — foi o que permitiu a
Fase 12 acrescentar o Cloudflare R2 sem tocar em `photo_service`.

Qual das duas vale é decidido por `STORAGE_BACKEND`. No Heroku o disco do
dyno é apagado a cada deploy e a cada restart diário, então lá `r2` não é
preferência: é a única opção que não perde as fotos.
"""

from __future__ import annotations

import mimetypes
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.core.config import settings

# Sem isto, .webp — que é o formato em que toda foto é gravada — seria
# enviado ao R2 como application/octet-stream, e o navegador se recusaria a
# exibi-lo como imagem.
mimetypes.add_type("image/webp", ".webp")

_TIPO_PADRAO = "application/octet-stream"
# Os nomes de arquivo carregam um sufixo aleatório e nunca são reaproveitados
# (ver `photo_service._caminho_novo`), então o conteúdo de uma URL jamais muda.
_CACHE_DAS_FOTOS = "public, max-age=31536000, immutable"


def _tipo_do_arquivo(rel_path: str) -> str:
    tipo, _ = mimetypes.guess_type(rel_path)
    return tipo or _TIPO_PADRAO


class Storage(Protocol):
    """Contrato mínimo: gravar, apagar, perguntar se existe e saber a URL."""

    def save(self, rel_path: str, data: bytes) -> str: ...

    def delete(self, rel_path: str) -> bool: ...

    def exists(self, rel_path: str) -> bool: ...

    def url_for(self, rel_path: str) -> str: ...


class LocalStorage:
    """Grava sob um diretório raiz — em desenvolvimento, o volume do Docker."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _resolver(self, rel_path: str) -> Path:
        """Impede que um caminho relativo escape da raiz.

        Sem isto, um `../../etc/algo` vindo de fora escreveria fora do volume.
        Hoje o caminho é sempre montado pela aplicação, mas a guarda custa
        três linhas e fecha a porta de vez.
        """
        raiz = self.root.resolve()
        destino = (raiz / rel_path).resolve()
        if not destino.is_relative_to(raiz):
            raise ValueError(f"Caminho fora do diretório de mídia: {rel_path}")
        return destino

    def save(self, rel_path: str, data: bytes) -> str:
        destino = self._resolver(rel_path)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(data)
        return rel_path

    def delete(self, rel_path: str) -> bool:
        """Devolve se havia mesmo um arquivo para apagar."""
        destino = self._resolver(rel_path)
        if not destino.exists():
            return False
        destino.unlink()
        return True

    def exists(self, rel_path: str) -> bool:
        return self._resolver(rel_path).exists()

    def url_for(self, rel_path: str) -> str:
        """O próprio caminho servido pela aplicação — nada a assinar."""
        return f"{settings.media_url_prefix}/{rel_path}"


class R2Storage:
    """Cloudflare R2, que fala o protocolo do S3.

    Escolhido por ser o mesmo provedor já previsto para os backups — uma conta
    a menos — e por não cobrar tráfego de saída, que num site de fotos é
    justamente o que costuma pesar.
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    @property
    def _cliente(self):  # noqa: ANN202 — o tipo real vem do botocore
        return get_r2_client()

    def save(self, rel_path: str, data: bytes) -> str:
        self._cliente.put_object(
            Bucket=self.bucket,
            Key=rel_path,
            Body=data,
            ContentType=_tipo_do_arquivo(rel_path),
            CacheControl=_CACHE_DAS_FOTOS,
        )
        return rel_path

    def delete(self, rel_path: str) -> bool:
        """Devolve se havia mesmo um objeto para apagar.

        O `delete_object` do S3 responde sucesso mesmo para chave inexistente,
        então a checagem antes é o que mantém a mesma semântica do disco.
        """
        if not self.exists(rel_path):
            return False
        self._cliente.delete_object(Bucket=self.bucket, Key=rel_path)
        return True

    def exists(self, rel_path: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._cliente.head_object(Bucket=self.bucket, Key=rel_path)
        except ClientError as erro:
            if erro.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise
        return True

    def url_for(self, rel_path: str) -> str:
        """URL pública do bucket, ou uma assinada e temporária se não houver.

        A URL assinada é o padrão porque funciona com o bucket fechado. Quando
        o bucket ganhar um domínio público, `R2_PUBLIC_BASE_URL` troca isso por
        uma URL estável e cacheável, sem mudar mais nada.
        """
        base = settings.r2_public_base_url.strip().rstrip("/")
        if base:
            return f"{base}/{rel_path}"
        return self._cliente.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": rel_path},
            ExpiresIn=settings.r2_url_expira_em,
        )


@lru_cache
def get_r2_client():  # noqa: ANN201 — o tipo real vem do botocore
    """Cliente do R2, criado uma vez só.

    O boto3 monta o cliente lendo arquivos de definição de serviço; refazer
    isso a cada upload custaria dezenas de milissegundos à toa.
    """
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        # O R2 não tem regiões; "auto" é o valor que ele espera.
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def get_storage() -> Storage:
    """Instância atual do armazenamento.

    Sem cache de propósito: os testes trocam `settings.media_root` por um
    diretório temporário e precisam que a troca valha na hora.
    """
    if settings.usa_r2:
        return R2Storage(settings.r2_bucket)
    return LocalStorage(settings.media_root)
