"""add_sighting_confirmation_metadata

Revision ID: b6f7c8d9e0f1
Revises: c4d8b6a92f10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6f7c8d9e0f1"
down_revision: str | Sequence[str] | None = "c4d8b6a92f10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing historical seed data only tracked a boolean confirmation flag.
    # Reset those rows before introducing metadata-backed confirmation constraints.
    op.execute("UPDATE sightings SET is_confirmed = 0 WHERE is_confirmed = 1")

    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("confirmed_by_ranger_id", sa.String(), nullable=True)
        )
        batch_op.add_column(sa.Column("confirmed_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_sightings_confirmed_by_ranger_id_rangers",
            "rangers",
            ["confirmed_by_ranger_id"],
            ["user_id"],
            ondelete="RESTRICT",
        )
        batch_op.create_check_constraint(
            "chk_sightings_confirmation_consistent",
            "(is_confirmed = 0 AND confirmed_by_ranger_id IS NULL "
            "AND confirmed_at IS NULL) OR "
            "(is_confirmed = 1 AND confirmed_by_ranger_id IS NOT NULL "
            "AND confirmed_at IS NOT NULL)",
        )
        batch_op.create_check_constraint(
            "chk_sightings_no_self_confirmation",
            "confirmed_by_ranger_id IS NULL OR confirmed_by_ranger_id <> ranger_id",
        )
        batch_op.create_index(
            "idx_sightings_confirmed_region_date_id",
            ["is_confirmed", "region", "date", "id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.drop_index("idx_sightings_confirmed_region_date_id")
        batch_op.drop_constraint(
            "chk_sightings_no_self_confirmation",
            type_="check",
        )
        batch_op.drop_constraint(
            "chk_sightings_confirmation_consistent",
            type_="check",
        )
        batch_op.drop_constraint(
            "fk_sightings_confirmed_by_ranger_id_rangers",
            type_="foreignkey",
        )
        batch_op.drop_column("confirmed_at")
        batch_op.drop_column("confirmed_by_ranger_id")
