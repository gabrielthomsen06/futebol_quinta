"""Dependências compartilhadas pelos routers.

`AdminDep` é a **única** porta de proteção do projeto. Nenhum router decodifica
JWT: proteger uma rota administrativa é anotar um parâmetro.

Dependência e não middleware, de propósito. Um middleware precisaria de uma
lista de caminhos públicos, que envelhece quando alguém acrescenta rota e
esquece de atualizá-la — e esse erro silencioso abre a rota em vez de fechá-la.
Aqui a proteção fica visível na assinatura da função e com cadeado no Swagger.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import TokenError, TokenExpiredError, decode_access_token
from app.db.session import get_session
from app.models.user import User
from app.services import auth_service

SessionDep = Annotated[Session, Depends(get_session)]

# auto_error=False para o erro ser nosso, no formato {"detail": ...} que o
# frontend já sabe ler, em vez do padrão do Starlette.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Token JWT obtido em POST /api/auth/login.",
)

BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_admin(session: SessionDep, credentials: BearerDep) -> User:
    """Exige um token válido e devolve o administrador correspondente."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Autenticação necessária.")

    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenExpiredError as erro:
        raise UnauthorizedError("Sua sessão expirou. Entre novamente.") from erro
    except TokenError as erro:
        raise UnauthorizedError("Credenciais inválidas.") from erro

    admin = auth_service.get_admin_by_id(session, user_id)
    if admin is None:
        # Token bem assinado de um usuário que não existe mais.
        raise UnauthorizedError("Credenciais inválidas.")

    return admin


AdminDep = Annotated[User, Depends(get_current_admin)]
