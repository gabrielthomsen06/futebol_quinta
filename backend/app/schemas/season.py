"""Contrato do seletor de temporadas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SeasonsRead(BaseModel):
    """Temporadas disponíveis e qual é a corrente.

    As duas informações vêm juntas de propósito: com o banco vazio, `available`
    é uma lista vazia e a tela ainda precisa saber que ano exibir.
    """

    current: int = Field(description="Temporada corrente, vinda da configuração da aplicação")
    available: list[int] = Field(
        description="Anos que têm partida em qualquer status, do mais recente ao mais antigo"
    )
