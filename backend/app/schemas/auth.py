"""Contratos de entrada e saída da autenticação."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Corpo de POST /api/auth/login."""

    username: str = Field(min_length=1, max_length=40)
    # Teto folgado de propósito: senha acima de 72 bytes precisa chegar ao
    # serviço para virar 401, e não ser barrada antes como 422.
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    """Token emitido no login."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: dt.datetime = Field(
        description="Quando o token deixa de valer. Evita que o frontend precise decodificar o JWT."
    )


class AuthUserRead(BaseModel):
    """Quem está autenticado: apenas identificador e nome de usuário."""

    # O hash da senha não é declarado neste schema, então não tem por onde
    # vazar numa resposta. Como comentário, e não docstring, para não ir
    # parar na descrição pública do OpenAPI.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
