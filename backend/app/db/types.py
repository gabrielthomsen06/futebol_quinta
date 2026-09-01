"""Tipos de coluna customizados."""

from enum import Enum
from typing import Any

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator


class EnumAsString(TypeDecorator[Any]):
    """Enum do Python persistido como VARCHAR.

    Decisão de arquitetura (D8): não usamos o tipo ENUM nativo do Postgres, que
    é penoso de alterar em migration. O domínio é garantido por um CHECK
    explícito na tabela e, no banco, a coluna é simplesmente VARCHAR — o que
    mantém model e migration descrevendo exatamente a mesma coisa.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_class: type[Enum], length: int) -> None:
        self.enum_class = enum_class
        super().__init__(length=length)

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return str(value.value)
        # Aceita a string crua, para comparação direta em consultas.
        return str(self.enum_class(value).value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Enum | None:
        if value is None:
            return None
        return self.enum_class(value)
