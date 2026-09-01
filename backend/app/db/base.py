"""Base declarativa e o mixin de timestamps usado por todas as tabelas.

Os models de domínio (players, matches, match_participations, users) chegam na
Fase 3 — aqui fica só a fundação que eles vão herdar.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Metadata compartilhada. É o que o Alembic compara com o banco."""


class TimestampMixin:
    """created_at / updated_at em UTC, mantidos pelo banco."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
