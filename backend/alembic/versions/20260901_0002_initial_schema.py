"""initial_schema — as quatro tabelas do domínio

Cria players, matches, match_participations e users com todas as constraints e
índices nomeados explicitamente. Constraint com nome gerado pelo banco é
impossível de alterar em migration futura sem antes descobrir como o Postgres
a batizou.

O que deliberadamente NÃO existe aqui:
  - nenhum contador agregado em players (total_goals, total_assists, ...);
  - nenhum UNIQUE em matches.match_date — duas partidas podem dividir a data;
  - nenhuma constraint ligando a soma dos gols individuais ao placar.

Revision ID: 0002_initial_schema
Revises: 0001_baseline
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_initial_schema"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("nickname", sa.String(length=40), nullable=False),
        sa.Column("photo_path", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=8),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_players"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_players_status",
        ),
        sa.CheckConstraint(
            "char_length(btrim(nickname)) > 0",
            name="ck_players_nickname_nao_vazio",
        ),
    )
    # Índice em expressão: o autogenerate do Alembic não gera este.
    op.create_index(
        "uq_players_nickname_lower",
        "players",
        [sa.text("lower(nickname)")],
        unique=True,
    )
    op.create_index("ix_players_status", "players", ["status"])

    op.create_table(
        "matches",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=12),
            server_default="SCHEDULED",
            nullable=False,
        ),
        sa.Column(
            "team_1_name", sa.String(length=40), server_default="TIME 1", nullable=False
        ),
        sa.Column(
            "team_2_name", sa.String(length=40), server_default="TIME 2", nullable=False
        ),
        sa.Column("team_1_score", sa.SmallInteger(), nullable=True),
        sa.Column("team_2_score", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_matches"),
        sa.CheckConstraint(
            "status IN ('SCHEDULED', 'PLAYED', 'CANCELLED')",
            name="ck_matches_status",
        ),
        sa.CheckConstraint(
            "(team_1_score IS NULL OR team_1_score >= 0)"
            " AND (team_2_score IS NULL OR team_2_score >= 0)",
            name="ck_matches_score_nao_negativo",
        ),
        sa.CheckConstraint(
            "status <> 'PLAYED'"
            " OR (team_1_score IS NOT NULL AND team_2_score IS NOT NULL)",
            name="ck_matches_played_tem_placar",
        ),
        sa.CheckConstraint(
            "char_length(btrim(team_1_name)) > 0"
            " AND char_length(btrim(team_2_name)) > 0",
            name="ck_matches_nomes_nao_vazios",
        ),
    )
    op.create_index("ix_matches_date", "matches", [sa.text("match_date DESC")])
    op.create_index(
        "ix_matches_status_date",
        "matches",
        ["status", sa.text("match_date DESC")],
    )

    op.create_table(
        "match_participations",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("team", sa.SmallInteger(), nullable=False),
        sa.Column("goals", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("assists", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_match_participations"),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
            name="fk_participations_match",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
            name="fk_participations_player",
            ondelete="RESTRICT",
        ),
        # Impede o jogador de aparecer duas vezes na mesma partida e,
        # por consequência, de estar nos dois times.
        sa.UniqueConstraint(
            "match_id", "player_id", name="uq_participations_match_player"
        ),
        sa.CheckConstraint("team IN (1, 2)", name="ck_participations_team"),
        sa.CheckConstraint("goals >= 0", name="ck_participations_goals"),
        sa.CheckConstraint("assists >= 0", name="ck_participations_assists"),
    )
    op.create_index("ix_participations_player", "match_participations", ["player_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=40), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )


def downgrade() -> None:
    # Ordem inversa: as dependentes primeiro.
    op.drop_table("users")
    op.drop_index("ix_participations_player", table_name="match_participations")
    op.drop_table("match_participations")
    op.drop_index("ix_matches_status_date", table_name="matches")
    op.drop_index("ix_matches_date", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_players_status", table_name="players")
    op.drop_index("uq_players_nickname_lower", table_name="players")
    op.drop_table("players")
