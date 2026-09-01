"""baseline — ponto zero do histórico de migrations

Revisão intencionalmente vazia. Ela existe para que `alembic upgrade head` rode
de ponta a ponta e crie a tabela `alembic_version` já na Fase 2, provando que a
cadeia de migrations funciona antes de existir qualquer schema.

O schema de verdade (players, matches, match_participations, users) entra na
Fase 3, como a revisão seguinte.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-01
"""

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
