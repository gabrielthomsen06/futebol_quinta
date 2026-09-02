"""Armazenamento de arquivos.

A interface existe para que trocar disco local por S3 no futuro seja escrever
outra classe, sem nenhum service mudar. O banco guarda apenas o caminho
relativo, então a troca também não exige migração de dados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.config import settings


class Storage(Protocol):
    """Contrato mínimo: gravar, apagar e perguntar se existe."""

    def save(self, rel_path: str, data: bytes) -> str: ...

    def delete(self, rel_path: str) -> bool: ...

    def exists(self, rel_path: str) -> bool: ...


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


def get_storage() -> Storage:
    """Instância atual do armazenamento.

    Sem cache de propósito: os testes trocam `settings.media_root` por um
    diretório temporário e precisam que a troca valha na hora.
    """
    return LocalStorage(settings.media_root)
