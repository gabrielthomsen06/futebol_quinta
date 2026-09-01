"""Base declarativa, convenção de nomes e o mixin de timestamps."""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Constraint com nome gerado pelo banco é impossível de alterar em migration
# futura sem antes descobrir como o Postgres a batizou. Esta convenção garante
# nome previsível para tudo que não for nomeado explicitamente.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    # Sem entrada "ck" de propósito: todo CHECK deste projeto é nomeado por
    # extenso no model, e qualquer template aqui prefixaria de novo, gerando
    # ck_ck_players_status. Sem a chave, o nome explícito passa intacto.
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Metadata compartilhada. É o que o Alembic compara com o banco."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """created_at / updated_at mantidos pelo banco."""

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
