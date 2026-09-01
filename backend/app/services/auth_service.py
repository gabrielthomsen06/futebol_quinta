"""Regras de autenticação do administrador único."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core import security
from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.repositories import user_repository

# Uma mensagem só para senha errada e para usuário inexistente. Diferenciar as
# duas transformaria o login num verificador de quais usuários existem.
CREDENCIAIS_INVALIDAS = "Usuário ou senha inválidos."


def authenticate(session: Session, username: str, password: str) -> User:
    """Valida usuário e senha, ou levanta 401.

    Quando o usuário não existe, ainda executamos uma verificação bcrypt contra
    um hash descartável: assim o tempo de resposta é o mesmo dos dois casos e
    não vaza a existência da conta por medição.
    """
    admin = user_repository.get_by_username(session, username.strip())

    if admin is None:
        security.verify_password(password, security.dummy_hash())
        raise UnauthorizedError(CREDENCIAIS_INVALIDAS)

    if not security.verify_password(password, admin.password_hash):
        raise UnauthorizedError(CREDENCIAIS_INVALIDAS)

    return admin


def get_admin_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    """Carrega o usuário do token.

    A dependência de proteção usa isto em vez de confiar apenas no conteúdo do
    token: um token continua válido só enquanto o usuário existir.
    """
    return user_repository.get_by_id(session, user_id)
