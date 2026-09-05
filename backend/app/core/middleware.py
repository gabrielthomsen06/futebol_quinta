"""O que o Caddy fazia e o roteador do Heroku não faz.

Na VPS, o Caddy era o único serviço exposto: ele terminava o TLS, redirecionava
HTTP para HTTPS, acrescentava os cabeçalhos de segurança, comprimia a resposta e
servia o React com fallback de SPA. O roteador do Heroku faz **só** a primeira
dessas coisas — ele encerra o TLS e repassa a requisição em HTTP simples, com o
esquema original no `X-Forwarded-Proto`.

Tudo o mais precisa voltar aqui dentro, senão a Fase 12 entregaria um site
funcional e sem nenhuma das proteções que a Fase 11 tinha conquistado.
"""

from __future__ import annotations

from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

# Os mesmos valores que estavam no Caddyfile, para que a migração não seja
# também uma mudança silenciosa de política.
CABECALHOS_DE_SEGURANCA = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# Caminhos que pertencem ao backend. Um 404 vindo deles é um 404 de verdade e
# precisa continuar sendo JSON — devolver a página do React no lugar faria uma
# rota de API errada parecer que funcionou.
PREFIXOS_DO_BACKEND = ("api/", "media/", "health", "docs", "redoc", "openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Acrescenta os cabeçalhos de segurança a toda resposta."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001, ANN201
        resposta: Response = await call_next(request)
        for nome, valor in CABECALHOS_DE_SEGURANCA.items():
            resposta.headers.setdefault(nome, valor)
        return resposta


class ForceHTTPSMiddleware(BaseHTTPMiddleware):
    """Redireciona HTTP para HTTPS lendo o cabeçalho que o proxy repassa.

    Ler o `X-Forwarded-Proto` na mão, em vez de confiar no esquema que o uvicorn
    deduz, faz o redirecionamento continuar correto mesmo que alguém suba a
    aplicação sem `--proxy-headers`.

    O 308 preserva o método — um POST redirecionado não vira GET — e é o mesmo
    código que o Caddy devolvia.
    """

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001, ANN201
        encaminhado = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
        esquema = encaminhado or request.url.scheme
        if esquema == "http":
            return RedirectResponse(
                str(request.url.replace(scheme="https")), status_code=308
            )
        return await call_next(request)


class SPAStaticFiles(StaticFiles):
    """Serve o React compilado e devolve o index.html no que não for arquivo.

    É o `try_files {path} /index.html` do Caddy. Sem ele, um F5 em
    `/jogadores/<id>` pediria ao servidor um arquivo que não existe e receberia
    404 — a rota só existe depois que o JavaScript do React carrega.
    """

    def __init__(self, diretorio: Path) -> None:
        super().__init__(directory=diretorio, html=True)

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        # A exceção precisa ser a do Starlette, não a do FastAPI: a do FastAPI
        # é uma subclasse dela, e é a classe-base que o StaticFiles levanta.
        # Capturar a errada faz todo F5 em rota interna devolver 404.
        except HTTPException as erro:
            if erro.status_code != 404 or path.startswith(PREFIXOS_DO_BACKEND):
                raise
            return await super().get_response("index.html", scope)
