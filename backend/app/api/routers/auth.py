"""Autenticação do administrador.

Dois endpoints, e nada além disso.

Não existe /logout de propósito: JWT é sem estado, e um endpoint que apenas
responde 200 não invalidaria token nenhum — quem tivesse copiado o token
continuaria entrando até o exp. Sair é o frontend descartar o token. Revogar de
verdade é trocar a SECRET_KEY, o que derruba todos os tokens de uma vez.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminDep, SessionDep
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import AuthUserRead, LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica o administrador",
    responses={401: {"description": "Usuário ou senha inválidos"}},
)
def login(dados: LoginRequest, session: SessionDep) -> TokenResponse:
    admin = auth_service.authenticate(session, dados.username, dados.password)
    token, expira_em = create_access_token(admin.id)
    return TokenResponse(access_token=token, expires_at=expira_em)


@router.get(
    "/me",
    response_model=AuthUserRead,
    summary="Quem está autenticado",
    responses={401: {"description": "Token ausente, inválido ou expirado"}},
)
def me(admin: AdminDep) -> User:
    return admin
