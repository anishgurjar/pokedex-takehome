"""unified_user_model

Revision ID: 7a60741dc732
Revises: 4235c1ee08ed

Restructures the user model:
  - Adds app_users (base table with role/email/display_name/status)
  - Drops and recreates trainers as a profile sub-table (user_id FK only)
  - Drops and recreates rangers as a profile sub-table (user_id FK + specialization)
  - Drops and recreates sightings to update ranger_id FK → rangers.user_id

For existing data: populate app_users before running this migration.
Fresh installs: just run `alembic upgrade head`.
"""

import contextlib
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a60741dc732"
down_revision: str | Sequence[str] | None = "4235c1ee08ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. New base user table                                               #
    # ------------------------------------------------------------------ #
    op.create_table(
        "app_users",
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("display_name_normalized", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=False),
        sa.Column("email_normalized", sa.String(length=256), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("role IN ('trainer', 'ranger')", name="chk_app_users_role"),
        sa.CheckConstraint(
            "status IN ('active', 'disabled')", name="chk_app_users_status"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("display_name_normalized"),
    )
    op.create_index(
        "idx_app_users_email_norm", "app_users", ["email_normalized"], unique=False
    )
    op.create_index(
        "idx_app_users_role_name",
        "app_users",
        ["role", "display_name_normalized"],
        unique=False,
    )

    # ------------------------------------------------------------------ #
    # 2. Drop pokemon.habitat leftover column                              #
    # ------------------------------------------------------------------ #
    # habitat was added then removed in earlier migrations; no-op if absent
    with op.batch_alter_table("pokemon") as batch_op, contextlib.suppress(Exception):
        batch_op.drop_column("habitat")

    # ------------------------------------------------------------------ #
    # 3. sightings depends on rangers — recreate both together             #
    #    SQLite cannot ALTER TABLE to change PKs or FKs in-place.         #
    # ------------------------------------------------------------------ #
    op.drop_table("sightings")
    op.drop_table("rangers")
    op.drop_table("trainers")

    op.create_table(
        "trainers",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "rangers",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("specialization", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "idx_rangers_specialization", "rangers", ["specialization"], unique=False
    )

    op.create_table(
        "sightings",
        sa.Column("pokemon_id", sa.Integer(), nullable=False),
        sa.Column("ranger_id", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("route", sa.String(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("weather", sa.String(), nullable=False),
        sa.Column("time_of_day", sa.String(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("is_shiny", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["pokemon_id"], ["pokemon.id"]),
        sa.ForeignKeyConstraint(["ranger_id"], ["rangers.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sightings")
    op.drop_index("idx_rangers_specialization", table_name="rangers")
    op.drop_table("rangers")
    op.drop_table("trainers")
    op.drop_index("idx_app_users_role_name", table_name="app_users")
    op.drop_index("idx_app_users_email_norm", table_name="app_users")
    op.drop_table("app_users")

    # Restore original flat tables
    op.create_table(
        "rangers",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("specialization", sa.String(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "trainers",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sightings",
        sa.Column("pokemon_id", sa.Integer(), nullable=False),
        sa.Column("ranger_id", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("route", sa.String(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("weather", sa.String(), nullable=False),
        sa.Column("time_of_day", sa.String(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("is_shiny", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["pokemon_id"], ["pokemon.id"]),
        sa.ForeignKeyConstraint(["ranger_id"], ["rangers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
