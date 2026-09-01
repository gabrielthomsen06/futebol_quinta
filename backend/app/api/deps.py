"""Dependências compartilhadas pelos routers.

get_current_admin (JWT) entra aqui na Fase 4.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]
