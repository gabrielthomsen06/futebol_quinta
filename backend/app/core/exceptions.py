"""Erros de domínio e a tradução deles para respostas HTTP.

O contrato com o frontend é sempre o mesmo formato — {"detail": "mensagem"} —
para que a interface possa exibir a mensagem do servidor direto no toast, sem
precisar traduzir código de erro na tela.
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Regra de negócio violada. Vira 400 por padrão."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(DomainError):
    """Choque com um dado que já existe (apelido repetido, por exemplo)."""

    status_code = status.HTTP_409_CONFLICT


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # O 422 do FastAPI é uma lista aninhada; achatamos para uma frase só,
        # mantendo os detalhes em "errors" para quem quiser investigar.
        first = exc.errors()[0] if exc.errors() else {}
        field = " → ".join(str(part) for part in first.get("loc", []) if part != "body")
        message = first.get("msg", "Dados inválidos.")
        detail = f"{field}: {message}" if field else message
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            # jsonable_encoder porque errors() pode trazer exceções no "ctx",
            # que o JSONResponse sozinho não serializa.
            content={"detail": detail, "errors": jsonable_encoder(exc.errors())},
        )
