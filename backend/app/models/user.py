"""Usuário administrador.

Tabela isolada: não se relaciona com nenhuma outra, porque o administrador não
é um jogador. Nesta fase existem apenas o model e o repository — login, hash e
JWT entram na Fase 4.
"""

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """O único administrador do MVP.

    É uma tabela, e não uma constante de configuração, para que trocar a senha
    sem redeploy seja barato.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    # bcrypt. A senha em texto puro nunca toca o banco nem o log.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.username}>"
